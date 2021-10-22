from asyncio import sleep, get_event_loop

from discord import Embed
from discord.ext import tasks

from song import Song
from youtube import download_audio_source
from util import random_color
from resource import save as resource_save, load as resource_load

count = -10

async def prepare(bot):
  res, dic = await resource_load('temps.json')
  await bot.wait_until_ready()
  if res:
    for guild in bot.guilds:
      for voice_channel in guild.voice_channels:
        if str(voice_channel.id) in dic.keys():
          await voice_channel.connect()
          
    for voice_client in bot.voice_clients:
      Player.players.append(Player(voice_client))

    for p in Player.players:
      player_dict = dic[str(p.voice_client.channel.id)]
      p.update(
        loop = player_dict['loop'],
        songs = player_dict['songs'],
        current = player_dict['current']
      )
      p.text_channel = bot.get_channel(int(player_dict['text_channel_id']))
      p.update(member = len(p.voice_client.channel.members))

  update.start()


async def on_update(p):
  p.idle = p.idle + 1 if not p.is_playing else 0
  p.idle2 = p.idle2 + 1 if p.member < 2 else 0

  if (p.idle > 600) or (p.idle2 > 240):
    await p.voice_client.disconnect()
    return

  if p.is_playing and p.voice_client and (p.voice_client.is_playing()):
    if p.played < p.songs[p.current].duration:
      p.played += 1

  if not p.task_block and p.voice_client and (len(p.songs) > 0) and not p.is_playing and (p.current < len(p.songs)):
    p.task_block = True
    await p.play()
    p.task_block = False


@tasks.loop(seconds = 1)
async def update():
  for p in Player.players:
    get_event_loop().create_task(on_update(p))

  global count
  count += 1
  if count > 30:
    dic = {}
    for p in Player.players:
      dic[str(p.voice_client.channel.id)] = p.to_dict()

    res, old_dic = await resource_load('temps.json')
    if res:
      if old_dic == dic:
        count = 0
        return

    await resource_save('temps.json', dic)
    count = 0


class Player:
  players = []

  @staticmethod
  def get_player(id):
    for player in Player.players:
      if player.voice_client.channel.id == id:
        return player
    for player in Player.players:
      if player.voice_client.guild.id == id:
        return player
    return None

  @staticmethod
  def get_players():
    return Player.players

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
    self.error_block = 0
    self.played = 0


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
    res, audio_source, song = await download_audio_source(song = self.songs[self.current])
    if not res:
      if self.text_channel:
        embed = Embed(
          title = f'🎵 {song.fixed_title(97)}',
          description = audio_source,
          url = song.url,
          color = random_color()
        )
        embed.set_author(name = '❗ Lỗi')
        embed.set_footer(text = 'Tự động phát bài tiếp theo trong 3 giây.')
        await self.text_channel.send(embed = embed, delete_after = 15)
      self.error_block = 3
      self.next()
      self.is_playing = False
      return
    
    self.is_playing = True
    self.played = 0
    if self.text_channel:
      embed = Embed(
        title = f'🎵 {song.fixed_title(97)}',
        description = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(97)}',
        url = song.url,
        color = random_color()
      )
      if song.thumbnail:
        embed.set_thumbnail(url = song.thumbnail)
      embed.set_author(name = '▶️ Đang phát')
      embed.set_footer(text = f'#️⃣ {self.current+1}/{len(self.songs)}')
      await self.text_channel.send(embed = embed, delete_after = float(song.duration + 3))
    if self.voice_client.is_playing():
      self.voice_client.stop()
    self.voice_client.play(audio_source, after = self.after_play)   

    
  def after_play(self, error = None):
    if error:
      if self.text_channel:
        song = self.songs[self.current]
        embed = Embed(
          title = f'🎵 {song.fixed_title(97)}',
          description = str(error),
          url = song.url,
          color = random_color()
        )
        embed.set_author(name = '❗ Lỗi')
        embed.set_footer(text = 'Tự động phát bài tiếp theo trong 3 giây.')
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

