from os import getenv
from discord.ext import commands
from discord import Embed, Intents, Activity, ActivityType
from dislash import InteractionClient, SelectMenu, SelectOption, ActionRow, Button, ButtonStyle

import youtube, player
from util import to_int, random_color
from song import from_dic
from random import shuffle
from pref import prepare, save_pref, load_pref

bot = commands.Bot(command_prefix = ['#', '$', '-'], intents = Intents.all())
bot.remove_command('help')
InteractionClient(bot)
player.bot = bot

  
@bot.event
async def on_voice_state_update(member, before, after):
  if member.id == bot.user.id:
    if not before.channel and after.channel:
      for voice_client in bot.voice_clients:
        if voice_client.channel.id == after.channel.id:
          player.players.append(player.Player(voice_client))
    if before.channel and not after.channel:
      p = player.find_channel(before.channel.id)
      if p:
        player.players.remove(p)
  for p in player.players:
    p.member = len(p.voice_client.channel.members)
       
        
@bot.event
async def on_ready():
  print(f'Logged as {bot.user.name}#{bot.user.discriminator} (ID: {bot.user.id})')
  await bot.change_presence(
    activity = Activity(
      type = ActivityType.listening, 
      name = "Watame Lullaby"
    )
  )
  await data_prepare()
  

help_page = 1
@bot.command(name = 'help', aliases = ['h'])
async def _help(ctx):
  def create_embed(page):
    embed = Embed(
      title = '📜 All commands',
      color = random_color()
    )
    if page == 1:
      embed.add_field(name = '#️⃣join/j', value = 'Join author\'s voice channel.', inline = False)
      embed.add_field(name = '#️⃣leave/l', value = 'Leave voice channel.', inline = False)
      embed.add_field(name = '#️⃣play/p <url/query>', value = 'Play an url or search for a song similar to query and play it. (YouTube only)', inline = False)
      embed.add_field(name = '#️⃣search/s/find/f <query>', value = 'Search a song with query. (YouTube only)', inline = False)
    elif page == 2:  
      embed.add_field(name = '#️⃣skip/next', value = 'Skip current song.', inline = False)
      embed.add_field(name = '#️⃣jump/move [index]', value = 'Jump to specific song in queue by index.', inline = False)
      embed.add_field(name = '#️⃣current/c', value = 'Show current song info.', inline = False) 
      embed.add_field(name = '#️⃣queue/q/playlist/list/all', value = 'Show queue.', inline = False)
      embed.add_field(name = '#️⃣remove/delete/del <index>', value = 'Remove a specific song in queue by index.', inline = False)
      embed.add_field(name = '#️⃣clear/clean/reset', value = 'Clear all songs in queue.', inline = False)
    else:
      embed.add_field(name = '#️⃣pause', value = 'Pause current song if playing.', inline = False)
      embed.add_field(name = '#️⃣resume', value = 'Resume current song if paused.', inline = False)
      embed.add_field(name = '#️⃣shuffle', value = 'Shuffle and play again the queue.', inline = False)
      embed.add_field(name = '#️⃣loop/repeat/r [mode]', value = 'Change loop/repeat mode of player: off/single/all', inline = False)
      embed.add_field(name = '#️⃣save <pref>', value = 'Save queue to a pref.', inline = False)
      embed.add_field(name = '#️⃣load <pref>', value = 'Load a pref and add all songs to queue.', inline = False)
    return embed
  
  global help_page
  help_page = 1
  embed = create_embed(help_page)
  components = [
    ActionRow(
      Button(
        style = ButtonStyle.blurple,
        label = "◀",
        custom_id = "left_button"
      ),
      Button(
        style = ButtonStyle.blurple,
        label = "▶",
        custom_id = "right_button"
      )
    )
  ]
  message = await ctx.send(embed = embed, components = components)
  on_click = message.create_click_listener(timeout = 60)

  @on_click.matching_id("left_button")
  async def on_left_button(inter):
    await inter.reply('Please wait...', delete_after = 0)
    global help_page
    help_page -= 1
    if help_page < 1:
      help_page = 1
    await inter.message.edit(embed = create_embed(help_page))
    
  @on_click.matching_id("right_button")
  async def on_right_button(inter):
    await inter.reply('Please wait...', delete_after = 0)
    global help_page
    help_page += 1
    if help_page > 3:
      help_page = 3
    await inter.message.edit(embed = create_embed(help_page))
    
  @on_click.timeout
  async def on_timeout():
    await message.edit(components=[])

@bot.command(name = 'join', aliases = ['j'])
async def _join(ctx):
  if not ctx.author.voice:
    embed = Embed(
      title = 'You are not connected to a voice channel.',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed)
    return
  
  await ctx.author.voice.channel.connect()
  await ctx.message.add_reaction('✅')
  
  
@bot.command(name = 'leave', aliases = ['l'])
async def _leave(ctx):
  for voice_client in bot.voice_clients:
    if voice_client.guild.id == ctx.author.guild.id:
      await voice_client.disconnect()
      await ctx.message.add_reaction('✅')

      
@bot.command(name = 'search', aliases = ['s', 'find', 'f'])
async def _search(ctx, *, query):
  res, urls = youtube.search(query, limit = 8)
  if not res:
    msg = urls
    embed = Embed(
      title = msg,
      color = random_color()
    )
    await ctx.send(embed)
    return
  
  options = []
  async with ctx.typing():
    for url in urls:
      res, song = await youtube.get_info(url)
      if res:
        options.append(SelectOption(label = song.fixed_title(1000), value = url, description = f'[{song.fixed_duration()}] - {song.fixed_uploader(1000)}'))
  components = [
    SelectMenu(
      custom_id = "search",
      placeholder = "Choose a song here to play",
      max_values = len(options),
      options = options
    )
  ]
  embed = Embed(
    title = f'Found {len(options)} song(s).',
    color = random_color()
  )
  message = await ctx.send(embed = embed, components = components, delete_after = 60)
  def check(inter):
    return inter.author == ctx.author
  try:
    inter = await message.wait_for_dropdown(check, timeout = 60)
    url = inter.select_menu.selected_options[0].value
    await message.delete(delay = 1) 
    await _play(ctx, text = url)
  except:
    return

  
@bot.command(name = 'play', aliases = ['p'])
async def _play(ctx, *, text):
  if not ctx.voice_client:
    if ctx.author.voice:
      await ctx.author.voice.channel.connect()
    else:
      embed = Embed(
        title = 'You are not connected to a voice channel.',
        color = random_color()
      )
      embed.set_author(name = '❗ Error')
      await ctx.send(embed = embed)
      return
    
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    embed = Embed(
      title = 'Something is wrong, please make bot rejoin voice channel to reset settings.',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  res, songs = None, None
  async with ctx.typing():
    if ('youtu.be' in text) or ('youtube.com' in text):
      if 'playlist?' in text:
        res, songs = await youtube.get_info_playlist(text)
      else:
        res, songs = await youtube.get_info(text)
        songs = [songs]
    else:
      if text.startswith('http') or text.startswith('www'):
        embed = Embed(
          title = 'Sorry this bot only support YouTube.'
        )
        embed.set_author(name = '❗ Error')
        await ctx.send(embed = embed)
      else:
        res2, urls = youtube.search(text)
        if res2:
          res, songs = await youtube.get_info(urls[0])
          songs = [songs]
        else:
          msg = urls
          embed = Embed(
            title = msg,
            color = random_color()
          )
          embed.set_author(name = '❗ Error')
          await ctx.send(embed = embed)
          return
  
  if not res:
    msg = songs
    embed = Embed(
      title = msg,
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  if len(songs) == 1:
    embed = Embed(
      title = songs[0].to_str(),
      url = songs[0].url,
      color = random_color()
    )
    embed.set_author(name = '⏏️ Enqueued')
    await ctx.send(embed = embed)
  else:
    embed = Embed(
      title = f'⏏️ Enqueued {len(songs)} songs.',
      color = random_color()
    )
    await ctx.send(embed = embed)
  p.text_channel = ctx.channel
  p.songs += songs

  
@bot.command(name = 'skip', aliases = ['next'])
async def _skip(ctx):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  
  if p.voice_client.is_playing():
    p.voice_client.stop()
  await ctx.message.add_reaction('✅')
    
    
@bot.command(name = 'jump', aliases = ['c', 'current', 'move'])
async def _jump(ctx, param = None):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'No songs in queue.',
      color = random_color()
    )
    await ctx.send(embed = embed)
    return
  
  if param == None:
    msg = 'No song found with current index.'
    url, thumbnail = None, None
    if p.current < len(p.songs):
      song = p.songs[p.current]
      msg = song.to_str()
      url = song.url
      if song.thumbnail:
        thumbnail = song.thumbnail
    embed = Embed(
      title = msg,
      color = random_color()
    )
    if url:
      embed.url = url
    if thumbnail:
      embed.set_thumbnail(url = thumbnail)
    embed.set_author(name = '▶️ Now playing')
    embed.set_footer(text = f'#️⃣ {p.current+1}/{len(p.songs)}')
    await ctx.send(embed = embed) 
  else:
    res, i = to_int(param)
    if not res:
      embed = Embed(
        title = f'Param {i} is not integer.',
        color = random_color()
      )
      embed.set_author(name = '❗ Error')
      await ctx.send(embed = embed)
      return
    
    i -= 1
    if (i < 0) or (i > len(p.songs)):
      embed = Embed(
        title = f'Param index {i+1} out of queue range {len(p.songs)}.',
        description = f'Current range: 1 -> {len(p.songs)}',
        color = random_color()
      )
      embed.set_author(name = '❗ Error')
      await ctx.send(embed = embed)
      return
    
    if p.voice_client.is_playing():
      p.jump_index = i
      p.voice_client.stop()
    else:
      p.current = i
    await ctx.message.add_reaction('✅')
      


     
@bot.command(name = 'queue', aliases = ['q', 'playlist', 'list', 'all'])
async def _queue(ctx):
  def create_embed(current_page, max_page): 
    embed = Embed(
      title = f'Page 🎵 {current_page} / {max_page}',
      color = random_color()
    )
    value = ''
    for i in range(0, 10):
      index = (current_page-1) * 10 + i
      if index < len(p.songs):
        field = f'[{index+1}] {p.songs[index].to_str()}'
        field = '▶️ ' + field if index == p.current else '#️⃣ ' + field
        value += field + '\n'
    name = 'Loop ↩️ Off'
    if p.loop == 1:
      name = 'Loop 🔂 Single'
    if p.loop == 2:
      name = 'Loop 🔁 All'
    embed.add_field(name = name, value = value, inline = True)
    return embed

  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'No songs in queue.',
      color = random_color()
    )
    await ctx.send(embed = embed)
    return
  
  p.max_page = (len(p.songs)-1) // 10 + 1
  p.current_page = p.current // 10 + 1
  embed = create_embed(p.current_page, p.max_page)
  components = [
    ActionRow(
      Button(
        style = ButtonStyle.blurple,
        label = "◀",
        custom_id = "left_button"
      ),
      Button(
        style = ButtonStyle.blurple,
        label = "▶",
        custom_id = "right_button"
      )
    )
  ]

  message = await ctx.send(embed = embed,  components = components)
  on_click = message.create_click_listener(timeout = 60)

  @on_click.matching_id("left_button")
  async def on_left_button(inter):
    await inter.reply('Please wait...', delete_after = 0)
    if len(p.songs) > 0:
      p.max_page = (len(p.songs)-1) // 10 + 1
      p.current_page -= 1
      if p.current_page < 1:
        p.current_page = 1
      await inter.message.edit(embed = create_embed(p.current_page, p.max_page))
    else:
      embed = Embed(
        title = 'No songs in queue.',
        color = random_color()
      )
      await inter.message.edit(embed = embed, components = [])

  @on_click.matching_id("right_button")
  async def on_right_button(inter):
    await inter.reply('Please wait...', delete_after = 0)
    if len(p.songs) > 0:
      p.max_page = (len(p.songs)-1) // 10 + 1
      p.current_page += 1
      if p.current_page > p.max_page:
        p.current_page = p.max_page
      await inter.message.edit(embed = create_embed(p.current_page, p.max_page))
    else:
      embed = Embed(
        title = 'No songs in queue.',
        color = random_color()
      )
      await inter.message.edit(embed = embed, components = [])

  @on_click.timeout
  async def on_timeout():
    await message.edit(components=[])


@bot.command(name = 'clear', aliases = ['clean', 'reset'])
async def _clear(ctx):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  
  if len(p.songs) > 0:
    p.songs.clear()
  if p.voice_client.is_playing():
    p.voice_client.stop()
  p.current = 0
  await ctx.message.add_reaction('✅')
  

@bot.command(name = 'remove', aliases = ['delete', 'del'])
async def _remove(ctx, param = None):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'No songs in queue.',
      color = random_color()
    ) 
    await ctx.send(embed = embed)
    return
  if param == None:
    embed = Embed(
      title = f'Type in index of the song to remove it from queue: remove [song_index]',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  res, i = to_int(param)
  if not res:
    embed = Embed(
      title = f'Param {i} is not integer.',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  i -= 1
  if (i < 0) or (i >= len(p.songs)):
    embed = Embed(
      title = f'Param index {i+1} out of queue range {len(p.songs)}.',
      description = f'Current range: 1 -> {len(p.songs)}',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  song = p.songs[i]
  p.songs.remove(p.songs[i])
  if i <= p.current:
    p.current -= 1
    if i == p.current:
      if p.voice_client.is_playing():
        p.voice_client.stop()
  embed = Embed(
    title = song.to_str(),
    url = song.url,
    color = random_color()
  )
  embed.set_author(name = '🧹 Removed')
  await ctx.send(embed = embed)
  
  
@bot.command(name = 'pause')
async def _pause(ctx):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  if not p.voice_client.is_paused():
    p.voice_client.pause()
    await ctx.message.add_reaction('⏸️')

    
@bot.command(name = 'resume')
async def _resume(ctx):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  if p.voice_client.is_paused():
    p.voice_client.resume()
    await ctx.message.add_reaction('▶️')

    
@bot.command(name = 'loop', aliases = ['repeat', 'r'])
async def _loop(ctx, param = None):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  
  if param == None:
    if p.loop == 0:
      p.loop = 1
    elif p.loop == 1:
      p.loop = 2
    else:
      p.loop = 0
  else:
    if param in ['0', 'off']:
      p.loop = 0
    elif param in ['1', 'single', 'one']:
      p.loop = 1
    elif param in ['2', 'all', 'queue']:
      p.loop = 2
    else:
      embed = Embed(
        title = 'Wrong param.',
        description = 'Correct param: \n↩️: 0/off\n🔂: 1/single/one\n🔁: 2/all/queue',
        color = random_color()
      )
      embed.set_author(name = '❗ Error')
      await ctx.send(embed = embed)
      return
  rc = '↩️'
  if p.loop == 1:
    rc = '🔂'
  if p.loop == 2:
    rc = '🔁'
  await ctx.message.add_reaction(rc)
  
  
@bot.command(name = 'shuffle')
async def _shuffle(ctx):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'No songs in queue.',
      color = random_color()
    )
    await ctx.send(embed = embed)
    return
  
  shuffle(p.songs)
  if p.voice_client.is_playing():
    p.voice_client.stop()
    p.current = -1
  else:
    p.current = 0
  await ctx.message.add_reaction('🔀')
    
@bot.command(name = 'save')
@commands.cooldown(1, 5, commands.BucketType.guild)
async def _save(ctx, *, pref = None):
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    return
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'No songs in queue.',
      color = random_color()
    )
    await ctx.send(embed = embed)
    return
  
  if (pref == None) or (pref == ''):
    embed = Embed(
      title = 'Need a name for queue to be saved.',
      description = 'Correct command: save [pref_name]',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  
  res, dic = await load_pref()
  if not res:
    embed = Embed(
      title = dic,
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  key = str(ctx.guild.id)
  pref = str(pref)
  if key not in dic:
    dic[key] = {}
  dic[key][pref] = []
  for song in p.songs:
    dic[key][pref].append(song.to_dic())

  await save_pref(dic)
  embed = Embed(
    title = f'📄 Current queue has been saved to pref:\n{pref}',
    color = random_color()
  )
  await ctx.send(embed = embed)
  
@bot.command(name = 'load')
@commands.cooldown(1, 5, commands.BucketType.guild)
async def _load(ctx, *, pref = None):
  if not ctx.voice_client:
    if ctx.author.voice:
      await ctx.author.voice.channel.connect()
    else:
      embed = Embed(
        title = 'You are not connected to a voice channel.',
        color = random_color()
      )
      embed.set_author(name = '❗ Error')
      await ctx.send(embed = embed)
      return
  p = player.find_guild(ctx.author.guild.id)
  if not p:
    embed = Embed(
      title = 'Something is wrong, please make bot rejoin voice channel to reset settings.',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  res, dic = await load_pref()
  key = str(ctx.guild.id)
  pref = str(pref)
  if key not in dic:
    embed = Embed(
      title = 'No pref saved on this guild.',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  if len(dic[key]) <= 0:
    embed = Embed(
      title = 'No pref saved on this guild.',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  if (pref == None) or (pref == ''):
    embed = Embed(
      title = 'Need pref name to be loaded.',
      description = f'All pref on this guild:\n{", ".join(dic[key].keys())}',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return
  
  if pref not in dic[key]:
    embed = Embed(
      title = f'No pref found in this guild with: {pref}.',
      description = f'All pref on this guild:\n{", ".join(dic[key].keys())}',
      color = random_color()
    )
    embed.set_author(name = '❗ Error')
    await ctx.send(embed = embed)
    return

  songs = []
  async with ctx.typing():
    for song_dic in dic[key][pref]:
      songs.append(from_dic(song_dic))
   
  embed = Embed(
    title = f'⏏️ Enqueued {len(songs)} songs from pref:\n{pref}.',
    color = random_color()
  )
  await ctx.send(embed = embed)
  p.text_channel = ctx.channel
  p.songs += songs
  
    
bot.loop.create_task(player._update(bot, 1))

TOKEN = getenv('token')
bot.run(TOKEN)
