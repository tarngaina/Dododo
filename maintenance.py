from os import getenv
from asyncio import get_event_loop
from traceback import format_exc as exc
from socket import gethostbyname, gethostname

from discord.ext import tasks
from discord import File
from github import Github

from util import now_str

GTOKEN = getenv('gtoken')
LOG_CHANNEL_ID = 891652708975673354
log_channel = None
restarting = False
count = 0
get_players = None

def is_restarting():
  global restarting
  return restarting


async def restart():
  global restarting
  if not restarting:
    restarting = True
    await log('Restarting bot.')
   
    try:
      g = Github(GTOKEN)
      repo = g.get_repo('tarngaina/dododo-bot')
      contents = repo.get_contents('version')
      repo.update_file(contents.path, "restart", str(now_str()), contents.sha, branch = 'main')
  
    except Exception as e:
      msg = f'{e}\n{exc()}'
      await log(msg)

  
@tasks.loop(seconds = 1)
async def update():
  global count
  count += 1
  if count > 32000:
    global get_players
    if get_players and (len(get_players()) == 0):
      await restart()
      

async def prepare(bot, gp):
  await bot.wait_until_ready()
  global get_players
  get_players = gp
  global log_channel
  log_channel = bot.get_channel(LOG_CHANNEL_ID)
  global restarting
  restarting = False
  update.start()
  await log(f'Deployed: {gethostbyname(gethostname())}')


async def log(text):
  if not log_channel:
    print('Warning: No log channel found.')
    return
    
  if len(text) > 1600:
    f = open('log.txt', 'w+', encoding = 'utf-8')
    f.write(text)
    f.close()
    await log_channel.send(f'{now_str()}', file = File('log.txt'))
  else:
    await log_channel.send(f'{now_str()}\n```\n{text}\n```')
