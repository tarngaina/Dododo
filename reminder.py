from os import getenv

OWNER_ID = getenv('owner_id')
owner = None

CHANNEL_ID = 890542648769806347
channel = None

async def data_prepare(bot):
  await bot.wait_until_ready()
  global owner, channel
  owner = bot.get_user(OWNER_ID)
  channel = bot.get_channel(CHANNEL_ID)
  print(owner.name, channel.name)
    
async def send():
  if not channel:
    return
  if not owner:
    return
  
  await channel.send(f'{owner.mention} deploy.')
