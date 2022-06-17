from os import getenv
from socket import gethostbyname, gethostname

from discord import File

from dododo.util import now_str


TOKEN = getenv('token')
LOG_CHANNEL_ID = 891652708975673354
log_channel = None


async def prepare(bot):
  global restarting
  restarting = False

  await bot.wait_until_ready()

  global log_channel
  log_channel = bot.get_channel(LOG_CHANNEL_ID)

  await log(f'Deployed: {gethostbyname(gethostname())}')


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
