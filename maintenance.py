from os import getenv
from asyncio import get_event_loop
from traceback import format_exc as exc

from discord.ext import tasks
from discord import File
from github import Github

from util import now


GTOKEN = getenv('gtoken')
LOG_CHANNEL_ID = 891652708975673354
log_channel = None
restarting = False
count = 0
bot_instance = None


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
      repo.update_file(contents.path, "restart", str(now()), contents.sha, branch = 'main')
  
    except Exception as e:
      msg = f'{e}\n{exc()}'
      await log(msg)

  
@tasks.loop(seconds = 1)
async def update():
  global count, bot_instance
  count += 1
  if count > 28000:
    if len(bot_instance.voice_clients) == 0:
      await restart()
      

async def prepare(bot):
  global bot_instance
  bot_instance = bot
  await bot.wait_until_ready()
  global log_channel
  log_channel = bot.get_channel(LOG_CHANNEL_ID)
  global restarting
  restarting = False
  update.start()
  await log('Deployed.')


async def log(text):
  if not log_channel:
    print('Warning: No log channel found.')
    return
    
  if len(text) > 1600:
    f = open('log.txt', 'w+', encoding = 'utf-8')
    f.write(text)
    f.close()
    await log_channel.send(f'{now()}', file = File('log.txt'))
  else:
    await log_channel.send(f'{now()}\n```\n{text}\n```')
