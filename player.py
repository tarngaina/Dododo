from discord import Embed
from asyncio import sleep, get_event_loop
from youtube import get_source
from util import random_color

players = []


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


async def on_update(p):
  if not p.is_playing:
    p.idle += 1
  else:
    p.idle = 0
  if p.member < 2:
    p.idle2 += 1
  else:
    p.idle2 = 0
  if (p.idle > 600) or (p.idle2 > 60):
    await p.voice_client.disconnect()
    return
  if (not p.task_block) and (len(p.songs) > 0) and (not p.is_playing) and (p.current < len(p.songs)):
    p.task_block = True
    await p.play()
    p.task_block = False

    
async def _update(bot, interval):
  await bot.wait_until_ready()
  while True:
    for p in players:
      get_event_loop().create_task(on_update(p))
    await sleep(interval)

    
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

    
  async def play(self):
    song = self.songs[self.current]
    res, audio_source, song = await get_source(song.url, song = song)
    if not res:
      if self.text_channel:
        msg = audio_source
        embed = Embed(
          title = f'{self.songs[self.current].to_str()}',
          description = msg,
          url = self.songs[self.current].url,
          color = random_color()
        )
        embed.set_author(name = '❗ Error')
        await self.text_channel.send(embed = embed)
        return
    if self.text_channel:
      embed = Embed(
        title = f'{song.to_str()}',
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
        embed = Embed(
          title = f'{self.songs[self.current].to_str()}',
          description = str(error),
          url = self.songs[self.current].url,
          color = random_color()
        )
        embed.set_author(name = '❗ Error')
        get_event_loop().run_until_complete(self.text_channel.send(embed = embed))
        return
      
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

 
