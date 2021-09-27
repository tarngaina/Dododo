from os import getenv
from datetime import datetime
from asyncio import get_event_loop
from traceback import format_exc as exc

from discord.ext import tasks
from discord import File
from github import Github

from youtube_dl import YoutubeDL


GTOKEN = getenv('gtoken')
LOG_CHANNEL_ID = 891652708975673354
log_channel = None
restarting = False
count = 0
ytdl_source = YoutubeDL(
  {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'verbose':False,
    'source_address': '0.0.0.0'
  }
)
get_players = None


async def restart():
  global restarting
  if not restarting:
    restarting = True
    await log('[maintenance.update]\nYoutube-DL error, restarting bot.')
    try:
      g = Github(GTOKEN)
      repo = g.get_repo('tarngaina/dododo-bot')
      contents = repo.get_contents('version')
      repo.update_file(contents.path, "restart", str(datetime.now()), contents.sha, branch = 'main')
    except Exception as e:
      print(exc())
      await log(exc())

  
@tasks.loop(minutes = 12)
async def update():
  global count
  if count > 0:
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_source.extract_info('https://youtu.be/wZGLkYVwcCs', download=False))
    if not data:
      restart()
  if count >= 40:
    if get_players:
      if len(get_players()) == 0:
        restart()
  count += 1

async def prepare(bot):
  await bot.wait_until_ready()
  global log_channel
  log_channel = bot.get_channel(LOG_CHANNEL_ID)
  global restarting
  restarting = False
  update.start()


def _log(text):
  get_event_loop().create_task(log(text))
    

async def log(text):
  if not log_channel:
    return
  if len(text) > 1000:
    f = open('temp.txt', 'w+', encoding = 'utf-8')
    f.write(text)
    f.close()
    await log_channel.send('too long', file = File('temp.txt'))
  else:
    await log_channel.send(f'```\n{text}\n```')
