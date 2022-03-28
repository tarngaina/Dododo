from os import getenv
from asyncio import get_event_loop, sleep
from traceback import format_exc as exc
from socket import gethostbyname, gethostname

import discord, logging
from discord.ext import tasks
from discord import File
from github import Github

from dododo.util import now_str

TOKEN = getenv('token')
GTOKEN = getenv('gtoken')
OWNER_ID = int(getenv('owner_id'))
LOG_CHANNEL_ID = 891652708975673354
LOG_CHANNEL_ID2 = 957822676670513162
log_channel = None
log_channel2 = None
restarting = False
count = 0
get_players = None


async def prepare(bot, get_players_func):
  global restarting
  restarting = False

  await bot.wait_until_ready()
  
  global get_players
  get_players = get_players_func

  global log_channel
  log_channel = bot.get_channel(LOG_CHANNEL_ID)
  
  global log_channel2
  log_channel2 = bot.get_channel(LOG_CHANNEL_ID2)

  update.start()
  start_discord_log()
  print('Deployed')
  await log(f'Deployed: {gethostbyname(gethostname())}')


@tasks.loop(seconds = 1)
async def update():
  global count
  count += 1
  if count > 32000:
    global get_players, restarting
    if get_players and (len(get_players()) == 0) and not restarting:
      await restart()


async def send_discord_log(text):
  if not log_channel2:
    print('Warning: No log2 channel found.')
    return
  
  await log_channel2.send(f'{now_str()}', text)


class ListHandler(logging.Handler): # Inherit from logging.Handler
  def __init__(self):
    # run the regular Handler __init__
    logging.Handler.__init__(self)

  def emit(self, record):
    # record.message is the log message
    get_event_loop().create_task(send_discord_log(record.msg))

def start_discord_log():
  logger = logging.getLogger('discord')
  logger.setLevel(logging.DEBUG)
  handler = ListHandler()
  handler.setFormatter(logging.Formatter('[%(asctime)s]:[%(levelname)s]:[%(name)s]: %(message)s'))
  logger.addHandler(handler)

def is_restarting():
  global restarting
  return restarting

async def restart():
  global restarting
  if not restarting:
    restarting = True
    await sleep(40)
    await log('Restarting bot.')
   
    try:
      g = Github(GTOKEN)
      repo = g.get_repo('tarngaina/dododo-bot')
      contents = repo.get_contents('version')
      repo.update_file(contents.path, "restart", str(now_str()), contents.sha, branch = 'main')
  
    except Exception as e:
      msg = f'{e}\n{exc()}'
      await log(msg)
    

async def log(text):
  if not log_channel:
    print('Warning: No log channel found.')
    return
    
  if len(text) > 1900:
    with open('log.txt', 'w+', encoding = 'utf-8') as f: 
      f.write(text)
    await log_channel.send(f'{now_str()}', file = File('log.txt'))
  else:
    await log_channel.send(f'{now_str()}\n```\n{text}\n```')
