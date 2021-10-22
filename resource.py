from json import loads, dump
from traceback import format_exc as exc

from discord import File, Forbidden

from system import log
from util import now_str

RESOURCE_CHANNEL_ID = 889792058565488660
resource_channel = None
RESOURCE_FILES = ['prefs.json', 'temps.json']
resource_messages = {}


async def prepare(bot):
  await bot.wait_until_ready()

  global resource_channel
  resource_channel = bot.get_channel(RESOURCE_CHANNEL_ID)

  await find_resource_messages()


async def find_resource_messages():
  global resource_messages
  if not resource_channel:
    return

  async for message in resource_channel.history(limit = len(RESOURCE_FILES) + 5):
    if message.attachments and (message.attachments[0].filename in RESOURCE_FILES):
      resource_messages[message.attachments[0].filename] = message
    
  for filename in RESOURCE_FILES:
    if filename not in resource_messages:
      with open(filename, 'w+', encoding = 'utf-8') as f:
        f.write('{}')
      resource_messages[filename] = await resource_channel.send(now_str(), file = File(filename))
        
      
async def load(filename):
  global resource_messages
  if not resource_channel:
    await log('No resource channel found.')
    return False, 'No resource channel found.'

  if filename not in resource_messages:
    await find_resource_messages()

  try:
    files = await resource_messages[filename].attachments[0].to_file()
    dic = loads(files.fp.read())
    return True, dic

  except Forbidden:
    await find_resource_messages()
    return False, 'Something is wrong right now, try again.'
  except Exception as e:
    msg = f'{e}\n{exc()}'
    await log(msg)
    return False, str(e)

async def save(filename, dic):
  global resource_messages
  if not resource_channel:
    await log('No resource channel found.')
    return False, 'No resource channel found.'

  if filename not in resource_messages:
    await find_resource_messages()

  try:
    with open(filename, 'w+', encoding = 'utf-8') as f:
      dump(dic, f, ensure_ascii = False, indent = 2)
    await resource_messages[filename].delete()
    resource_messages[filename] = await resource_channel.send(now_str(), file = File(filename))
    return True, ''

  except Forbidden:
    await find_resource_messages()
    return False, 'Something is wrong right now, try again.'
  except Exception as e:
    msg = f'{e}\n{exc()}'
    await log(msg)
    return False, str(e)


