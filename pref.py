CHANNEL_ID = 889792058565488660
data_channel = None
data_message = None


from discord import File
from json import loads, dump


def find_data_channel(bot):
  global data_channel
  for guild in bot.guilds:
    for channel in guild.channels:
      if channel.id == CHANNEL_ID:
        data_channel = channel


async def find_data_message():
  global data_message
  if not data_channel:
    return

  async for message in data_channel.history(limit = 4):
    if (message.content == 'read') and message.attachments:
      data_message = message
      break
      
  if not data_message:
    with open(f'data.json', 'w+', encoding = 'utf-8') as f:
      dump(dic, f, ensure_ascii = False, indent = 2)
    data_message = await data_channel.send('read', file = File('data.json'))
        
async def load_pref():
  if not data_channel:
    return False, 'No data source found.'
  
  if not data_message:
    await find_data_message()

  try:
    files = await data_message.attachments[0].to_file()
    dic = json.loads(files.fp.read())
    return True, dic
  except Exception as e:
    return False, str(e)

async def save_pref(dic):
  global data_message
  if not data_channel:
    return False, 'No data source found.'

  if not data_message:
    await find_data_message()

  try:
    with open(f'data.json', 'w+', encoding = 'utf-8') as f:
      json.dump(dic, f, ensure_ascii = False, indent = 2)
    await data_message.delete()
    data_message = await data_channel.send('read', file = File('data.json'))
    return True, ''
  except Exception as e:
    return False, str(e)


