from asyncio import sleep, get_event_loop

from discord import Embed
from discord.ext import tasks

from song import Song
from youtube import get_source
from util import random_color
from resource import save, load

players = []
count = -10

def add_player(voice_client):
  players.append(Player(voice_client))
  
def remove_player(player):
  players.remove(player)

def get_player(id):
  p = find_channel(id)
  if not p:
    p = find_guild(id)
  return p

def find_channel(id):
  for player in players:
    if player.voice_client.channel.id == id:
      return player
  return None

def find_guild(id):
  for player in players:
    if player.voice_client.guild.id == id:
      return player
  return None

def get_players():
  return players


async def on_update(p):
  if not p.is_playing:
    p.idle += 1
  else:
    p.idle = 0
  if p.member < 2:
    p.idle2 += 1
  else:
    p.idle2 = 0
  if (p.idle > 600) or (p.idle2 > 300):
    await p.voice_client.disconnect()
    return
  if (not p.task_block) and (len(p.songs) > 0) and (not p.is_playing) and (p.current < len(p.songs)):
    p.task_block = True
    await p.play()
    p.task_block = False
    

@tasks.loop(seconds = 1)
async def update():
  global count
  count += 1
  for p in players:
    get_event_loop().create_task(on_update(p))
  if count > 30:
    dic = {}
    for p in players:
      dic[str(p.voice_client.channel.id)] = p.to_dict()
    await save('temps.json', dic)
    count = 0

async def prepare(bot):
  res, dic = await load('temps.json')
  await bot.wait_until_ready()
  if res:
    for guild in bot.guilds:
      for voice_channel in guild.voice_channels:
        if str(voice_channel.id) in dic.keys():
          await voice_channel.connect()
          
    for voice_client in bot.voice_clients:
      add_player(voice_client)
    for p in get_players():
      player_dict = dic[str(p.voice_client.channel.id)]
      p.update(
        loop = player_dict['loop'],
        songs = player_dict['songs'],
        current = player_dict['current']
      )
      p.text_channel = bot.get_channel(int(player_dict['text_channel_id']))
      p.update(member = len(p.voice_client.channel.members))
  update.start()


class Player:
  def __init__(self, voice_client):
    self.voice_client = voice_client
    self.text_channel = None

    self.loop = 0 
    self.songs = []
    self.current = 0

    self.is_playing = False
    self.idle = 0
    self.idle2 = 0
    self.member = 0
    self.task_block = False
    self.current_page = 0
    self.max_page = 0
    self.error_block = 0


  def update(self, **dic):
    if 'loop' in dic:
      self.loop = int(dic['loop'])
    if 'current' in dic:
      self.current = int(dic['current'])
    if 'songs' in dic:
      for song_dict in dic['songs']:
        self.songs.append(Song.from_dict(song_dict))
    if 'member' in dic:
      self.member = int(dic['member'])
    
  
  def to_dict(self):
    dic = {}
    if self.text_channel:
      dic['text_channel_id'] = str(self.text_channel.id)
    dic['loop'] = str(self.loop)
    dic['current'] = str(self.current)
    dic['songs'] = []
    for song in self.songs:
      dic['songs'].append(song.to_dict())
    return dic

  async def play(self):
    if self.error_block > 0:
      self.error_block -= 1
      return
    song = self.songs[self.current]
    res, audio_source, song = await get_source(song.url, song = song)
    if not res:
      if self.text_channel:
        msg = audio_source
        embed = Embed(
          title = f'🎵 {song.fixed_title(1000)}',
          description = msg,
          url = self.songs[self.current].url,
          color = random_color()
        )
        embed.set_author(name = '❗ Error')
        embed.set_footer(text = 'Atuo skip to next song in 3 seconds.')
        await self.text_channel.send(embed = embed, delete_after = 20)
      self.error_block = 3
      self.next()
      self.is_playing = False
      return
    
    if self.text_channel:
      embed = Embed(
        title = f'🎵 {song.fixed_title(1000)}',
        description = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(1000)}',
        url = song.url,
        color = random_color()
      )
      if song.thumbnail:
        embed.set_thumbnail(url = song.thumbnail)
      embed.set_author(name = '▶️ Now playing')
      embed.set_footer(text = f'#️⃣ {self.current+1}/{len(self.songs)}')
      await self.text_channel.send(embed = embed, delete_after = float(song.duration + 3))
    self.is_playing = True
    if self.voice_client.is_playing():
      self.voice_client.stop()
    self.voice_client.play(audio_source, after = self.after_play)   

    
  def after_play(self, error=None):
    if error:
      if self.text_channel:
        song = self.songs[self.current]
        embed = Embed(
          title = f'🎵 {song.fixed_title(1000)}',
          description = str(error),
          url = song.url,
          color = random_color()
        )
        embed.set_author(name = '❗ Error')
        embed.set_footer(text = 'Gonna skip to next song in 3 seconds.')
        get_event_loop().create_task(self.text_channel.send(embed = embed))
      self.error_block = 3
      
    self.next()
    self.is_playing = False

  def next(self):
    if self.loop != 1:
      self.current += 1
      if self.current > len(self.songs):
        self.current = len(self.songs)
      if self.loop == 2:
        if self.current >= len(self.songs):
          self.current = 0
    else:
      if self.current >= len(self.songs):
        self.current = len(self.songs)-1

