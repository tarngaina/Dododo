from os import getenv
from random import shuffle

from discord.ext import commands
from discord import Embed, Intents, Activity, ActivityType
from dislash import InteractionClient, SelectMenu, SelectOption, ActionRow, Button, ButtonStyle
from asyncio import sleep

from player import prepare as player_prepare, get_player, get_players, add_player, remove_player
from song import Song
from youtube import search as youtube_search, get_info, get_info_playlist
from util import to_int, random_color
from resource import prepare as resource_prepare, load as resource_load, save as resource_save
from maintenance import prepare as maintenance_prepare, restart, is_restarting

bot = commands.Bot(command_prefix = ['#', '$', '-'], case_insensitive = True, intents = Intents.all())
bot.remove_command('help')
InteractionClient(bot)
OWNER_ID = int(getenv('owner_id'))


@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandNotFound):
    embed = Embed(
      title = 'Không tìm thấy lệnh.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
  if isinstance(error, commands.CommandOnCooldown):
    embed = Embed(
      title = f'Thử lại sau {error.retry_after:.2f} giây.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
  
  
@bot.event
async def on_voice_state_update(member, before, after):
  if member.id == bot.user.id:
    if not before.channel and after.channel:
      for voice_client in bot.voice_clients:
        if voice_client.channel.id == after.channel.id:
          add_player(voice_client)
    if before.channel and not after.channel:
      p = get_player(before.channel.id)
      if p:
        remove_player(p)
  for p in get_players():
    p.member = len(p.voice_client.channel.members)
       
        
@bot.event
async def on_ready():
  await bot.wait_until_ready()
  await bot.change_presence(
    activity = Activity(
      type = ActivityType.listening, 
      name = "Watame Lullaby"
    )
  )
  await resource_prepare(bot)
  await maintenance_prepare(bot, get_players)
  await player_prepare(bot)


@bot.command(name = 'restart')
async def _restart(ctx):
  if ctx.author.id == OWNER_ID:
    await restart()
    await ctx.message.add_reaction('✅')
  else:
    embed = Embed(
      title = 'Ôi bạn ơi, bạn chưa đủ sức mạnh để làm chủ cái này.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)


help_page = 1
@bot.command(name = 'help', aliases = ['h', 'giúp'])
async def _help(ctx):
  def create_embed(page):
    embed = Embed(
      title = f'📄 {page}/{4}',
      color = random_color()
    )
    if page == 1:
      embed.add_field(name = '#️⃣ join/j', value = '✅ Vào voice.', inline = False)
      embed.add_field(name = '#️⃣ leave/l', value = '❎ Thoát voice.', inline = False)
      embed.add_field(name = '#️⃣ play/p/enqueue <link/từ khoá>', value = '⏏️ Phát bài hát từ link hoặc từ khoá.', inline = False)
      embed.add_field(name = '#️⃣ search/s/find/f <từ khoá>', value = '🔎 Tìm bài hát, chọn để phát nhạc.', inline = False)
    elif page == 2:  
      embed.add_field(name = '#️⃣ queue/q/playlist/list/all', value = '📄 Xem danh mục phát..', inline = False)
      embed.add_field(name = '#️⃣ current/c/info/i/now', value = 'ℹ️ Xem bài đang phát.', inline = False) 
      embed.add_field(name = '#️⃣ previous/prev/back/bacc', value = '⏮️ Phát bài trước đó.', inline = False)
      embed.add_field(name = '#️⃣ next/skip', value = '⏭️ Phát bài tiếp theo.', inline = False)
      embed.add_field(name = '#️⃣ jump/move <vị trí>', value = '⤵️ Nhảy tới bài được chọn và phát.', inline = False)
      embed.add_field(name = '#️⃣ remove/delete/del <vị trí>', value = '🧹 Xóa bài được chọn.', inline = False)
      embed.add_field(name = '#️⃣ clear/clean/reset', value = '🧹 Dừng và xóa tất cả bài hát.', inline = False)
    elif page == 3:  
      embed.add_field(name = '#️⃣ pause/stop', value = '⏸️ Tạm dừng phát nhạc..', inline = False)
      embed.add_field(name = '#️⃣ resume/continue', value = '▶️ Tiếp tục phát nhạc.', inline = False)
      embed.add_field(name = '#️⃣ shuffle', value = '🔀 Trộn danh mục phát và phát lại từ đầu.', inline = False)
      embed.add_field(name = '#️⃣ loop/repeat/r [chế độ]', value = '🔁 Chế độ lặp lại: tắt/một/tất cả', inline = False)
    else:
      embed.add_field(name = '#️⃣ save <tên>', value = '📄 Lưu danh mục phát.', inline = False)
      embed.add_field(name = '#️⃣ load <tên>', value = '📄 Tải danh mục phát đã lưu.', inline = False)
      embed.add_field(name = '#️⃣ forget <tên>', value = '📄 Xoá danh mục phát đã lưu.', inline = False)
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
  on_click = message.create_click_listener(timeout = 300)

  @on_click.matching_id("left_button")
  async def on_left_button(inter):
    await inter.reply('Đợi xíu...', delete_after = 0)
    global help_page
    help_page -= 1
    if help_page < 1:
      help_page = 1
    await inter.message.edit(embed = create_embed(help_page))
    
  @on_click.matching_id("right_button")
  async def on_right_button(inter):
    await inter.reply('Đợi xíu...', delete_after = 0)
    global help_page
    help_page += 1
    if help_page > 4:
      help_page = 4
    await inter.message.edit(embed = create_embed(help_page))
    
  @on_click.timeout
  async def on_timeout():
    await message.edit(components=[])


@bot.command(name = 'join', aliases = ['j', 'vào'])
async def _join(ctx):
  if not ctx.author.voice:
    embed = Embed(
      title = 'Chưa vô voice bạn ơi.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed)
    return
  
  await ctx.author.voice.channel.connect()
  await ctx.message.add_reaction('✅')
  
  
@bot.command(name = 'leave', aliases = ['l', 'thoát'])
async def _leave(ctx):
  for voice_client in bot.voice_clients:
    if voice_client.guild.id == ctx.author.guild.id:
      await voice_client.disconnect()
      await ctx.message.add_reaction('❎')

      
@bot.command(name = 'search', aliases = ['s', 'find', 'f', 'tìm'])
async def _search(ctx, *, query):  
  if (query == None) or (query == ''):
    embed = Embed(
      title = 'Nhập từ khoá đi bạn.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  res, urls = youtube_search(query)
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
      if len(options) > 9:
        break
      res, song = await get_info(url)
      if res:
        options.append(SelectOption(label = f'🎵 {song.fixed_title(1000)}', value = url, description = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(1000)}'))
  
  components = [
    SelectMenu(
      custom_id = 'search',
      placeholder = 'Bấm đây để chọn bài hát',
      max_values = len(options),
      options = options
    )
  ]
  embed = Embed(
    title = f'Tìm thấy {len(options)} bài.',
    color = random_color()
  )
  message = await ctx.send(embed = embed, components = components, delete_after = 60)

  try:
    inter = await message.wait_for_dropdown(timeout = 300)
    url = inter.select_menu.selected_options[0].value
    await message.delete(delay = 1) 
    await _play(ctx, text = url)
  except:
    return

  
@bot.command(name = 'play', aliases = ['p', 'enqueue', 'phát'])
async def _play(ctx, *, text):
  if is_restarting():
    embed = Embed(
      title = 'Đợi 2 phút bạn, bot đang restart.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  if not ctx.voice_client:
    if ctx.author.voice:
      await ctx.author.voice.channel.connect()
    else:
      embed = Embed(
        title = 'Vô voice bạn ơi.',
        color = random_color()
      )
      embed.set_author(name = '❗ Lỗi')
      await ctx.send(embed = embed)
      return
    
  p = get_player(ctx.author.guild.id)
  if not p:
    embed = Embed(
      title = 'Lỗi rồi, cho bot thoát ra vào lại voice đi bạn.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  if (text == None) or (text == ''):
    embed = Embed(
      title = 'Nhập link hay từ khoá bạn ơi.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  songs = []
  infos = {}
  async with ctx.typing():
    if ('youtu.be' in text) or ('youtube.com' in text):
      if 'playlist?' in text:
        res, songs, infos = await get_info_playlist(text)
        if not res:
          embed = Embed(
            title = songs,
            color = random_color()
          )
          embed.set_author(name = '❗ Lỗi')
          await ctx.send(embed = embed)
          return
      else:
        res, songs = await get_info(text)
        if not res:
          embed = Embed(
            title = songs,
            color = random_color()
          )
          embed.set_author(name = '❗ Lỗi')
          await ctx.send(embed = embed)
          return
        songs = [songs]
    else:
      if text.startswith('http') or text.startswith('www'):
        embed = Embed(
          title = 'Chỉ hỗ trợ YouTube.',
          color = random_color()
        )
        embed.set_author(name = '❗ Lỗi')
        await ctx.send(embed = embed)
        return
      else:
        res, urls = youtube_search(text)
        if not res:
          embed = Embed(
            title = urls,
            color = random_color()
          )
          embed.set_author(name = '❗ Lỗi')
          await ctx.send(embed = embed)
          return
        res, songs = await get_info(urls[0])
        if not res:
          embed = Embed(
            title = songs,
            color = random_color()
          )
          embed.set_author(name = '❗ Lỗi')
          await ctx.send(embed = embed)
          return
        songs = [songs]
          
  if len(songs) == 0:
    embed = Embed(
      title = 'Link lỗi.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  if len(songs) == 1:
    embed = Embed(
      title = f'🎵 {songs[0].fixed_title(1000)}',
      description = f'🕒 {songs[0].fixed_duration()} 👤 {songs[0].fixed_uploader(1000)}',
      url = songs[0].url,
      color = random_color()
    )
    embed.set_author(name = '⏏️ Đang chờ phát')
    if songs[0].thumbnail:
      embed.set_thumbnail(url = songs[0].thumbnail)
    embed.set_footer(text = f'#️⃣ {len(p.songs)+1}/{len(p.songs)+1}')
    await ctx.send(embed = embed)
  else:
    embed = Embed(
      title = f'🎵 {len(songs)} bài trong 📄 {infos["title"]} 👤 {infos["uploader"]}',
      url = infos['url'],
      color = random_color()
    )
    embed.set_thumbnail(url = infos['thumbnail'])
    embed.set_author(name = '⏏️ Đang chờ phát')
    embed.set_footer(text = f'#️⃣ {len(p.songs)+1}/{len(p.songs)+len(songs)}')
    await ctx.send(embed = embed)
  p.text_channel = ctx.channel
  p.songs += songs


@bot.command(name = 'back', aliases = ['prev', 'previous', 'bacc', 'lùi', 'lui'])
async def _back(ctx):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
  
  if p.voice_client.is_playing():
    if p.current - 2 < -1:
      p.current = -1
    else:
      p.current -= 2
    p.voice_client.stop()
  await ctx.message.add_reaction('⏮')

  
@bot.command(name = 'skip', aliases = ['next', 'tới'])
async def _skip(ctx):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
  
  if p.voice_client.is_playing():
    p.voice_client.stop()
  await ctx.message.add_reaction('⏭️')
    

@bot.command(name = 'current', aliases = ['c', 'now', 'info', 'i', 'đang'])
async def _current(ctx):
  def create_embed(p):
    if len(p.songs) <= 0:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      return embed

    song = p.songs[p.current]
    embed = Embed(
      title = f'🎵 {song.fixed_title(1000)}',
      description = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(1000)}\n📅 {song.fixed_upload_date()} 📊 {song.fixed_view_count()} 👍 {song.fixed_like_count()}\n{song.fixed_description()}',
      url = song.url,
      color = random_color()
    )
    if song.thumbnail:
      embed.set_thumbnail(url = song.thumbnail)
    embed.set_author(name = '▶️ Đang phát')
    embed.set_footer(text = f'#️⃣ {p.current+1}/{len(p.songs)}')
    return embed

  p = get_player(ctx.author.guild.id)
  if not p:
    return

  embed = create_embed(p)
  components = [
    ActionRow(
      Button(
        style = ButtonStyle.blurple,
        label = "<<",
        custom_id = "previous_button"
      ),
      Button(
        style = ButtonStyle.blurple,
        label = "❚❚",
        custom_id = "pause_button"
      ),
      Button(
        style = ButtonStyle.blurple,
        label = "▶",
        custom_id = "resume_button"
      ),
      Button(
        style = ButtonStyle.blurple,
        label = ">>",
        custom_id = "next_button"
      )
    )
  ]
  message = await ctx.send(embed = embed, components = components)
  on_click = message.create_click_listener(timeout = 300)

  @on_click.matching_id("previous_button")
  async def on_left_button(inter):
    p = get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return

    sec = 3
    await inter.reply('Đợi tý...', delete_after = sec)
    await _back(inter)
    await sleep(sec)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])
    
  @on_click.matching_id("next_button")
  async def on_right_button(inter):
    p = get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return 

    sec = 3
    await inter.reply('Đợi tý...', delete_after = sec)
    await _skip(inter)
    await sleep(sec)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])

  @on_click.matching_id("pause_button")
  async def on_right_button(inter):
    p = get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return

    await inter.reply('Đợi tý...', delete_after = 0)
    await _pause(inter)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])

  @on_click.matching_id("resume_button")
  async def on_right_button(inter):
    p = get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return

    await inter.reply('Đợi tý...', delete_after = 0)
    await _resume(inter)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])
    
  @on_click.timeout
  async def on_timeout():
    await message.edit(components=[])


@bot.command(name = 'jump', aliases = ['move', 'nhảy', 'đến'])
async def _jump(ctx, param = None):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
    
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'Không có bài nào.',
      color = random_color()
    )
    await ctx.send(embed = embed)
    return
  
  if param == None:
    embed = Embed(
      title = f'Nhập vị trí bài hát bạn ơi.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  res, i = to_int(param)
  if not res:
    embed = Embed(
      title = f'{i} không phải là số hay vị trí.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
    
  i -= 1
  if (i < 0) or (i > len(p.songs)):
    embed = Embed(
      title = f'Vị trí tào lao: {i+1}.',
      description = f'Hợp lệ: từ 1 đến {len(p.songs)}',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
    
    
  if p.voice_client.is_playing():
    p.current = i-1
    p.voice_client.stop()
  else:
    p.current = i
  await ctx.message.add_reaction('⤵️')
      
     
@bot.command(name = 'queue', aliases = ['q', 'playlist', 'list', 'all'])
async def _queue(ctx):
  def create_embed(current_page, max_page): 
    embed = Embed(
      title = f'📄 {current_page} / {max_page}',
      color = random_color()
    )
    value = ''
    for i in range(0, 10):
      index = (current_page-1) * 10 + i
      if index < len(p.songs):
        song = p.songs[index]
        embed.add_field(name = f'{"▶️ " if index == p.current else "#️⃣ "} {index+1} 🎵 {song.fixed_title(1000)}', value = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(1000)}', inline = False)
    duration = 0
    for song in p.songs:
      duration += song.duration
    text = f'#️⃣ {len(p.songs)} bài được phát trong 🕒 {Song(duration = duration).fixed_duration()}'
    loop = '↩️ Tắt'
    if p.loop == 1:
      loop = '🔂 Một'
    if p.loop == 2:
      loop = '🔁 Tất cả'
    text = loop + ' ' + text   
    embed.set_footer(text = text)
    return embed

  p = get_player(ctx.author.guild.id)
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
  on_click = message.create_click_listener(timeout = 120)

  @on_click.matching_id("left_button")
  async def on_left_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      p.max_page = (len(p.songs)-1) // 10 + 1
      p.current_page -= 1
      if p.current_page < 1:
        p.current_page = 1
      await inter.message.edit(embed = create_embed(p.current_page, p.max_page))
    else:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      await inter.message.edit(embed = embed, components = [])

  @on_click.matching_id("right_button")
  async def on_right_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      p.max_page = (len(p.songs)-1) // 10 + 1
      p.current_page += 1
      if p.current_page > p.max_page:
        p.current_page = p.max_page
      await inter.message.edit(embed = create_embed(p.current_page, p.max_page))
    else:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      await inter.message.edit(embed = embed, components = [])

  @on_click.timeout
  async def on_timeout():
    await message.edit(components=[])


@bot.command(name = 'clear', aliases = ['clean', 'reset', 'dẹp'])
async def _clear(ctx):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
  
  if len(p.songs) > 0:
    p.songs.clear()
  if p.voice_client.is_playing():
    p.voice_client.stop()
  p.current = 0
  await ctx.message.add_reaction('🧹')
  

@bot.command(name = 'remove', aliases = ['delete', 'del', 'xóa'])
async def _remove(ctx, param = None):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'Không có bài nào.',
      color = random_color()
    ) 
    await ctx.send(embed = embed)
    return
  if param == None:
    embed = Embed(
      title = f'Nhập vị trí bài hát đi bạn.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  res, i = to_int(param)
  if not res:
    embed = Embed(
      title = f'{i} không phải là số hay vị trí.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  i -= 1
  if (i < 0) or (i >= len(p.songs)):
    embed = Embed(
      title = f'Vị trí nhảm nhí: {i+1}.',
      description = f'Hợp lệ: từ 1 đến {len(p.songs)}',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  song = p.songs.pop(i)
  if i <= p.current:
    if i == p.current:
      if p.voice_client.is_playing():
        p.voice_client.stop()
    p.current -= 1
  embed = Embed(
    title = f'🎵 {song.fixed_title(1000)}',
    description = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(1000)}',
    url = song.url,
    color = random_color()
  )
  if song.thumbnail:
    embed.set_thumbnail(url = song.thumbnail)
  embed.set_author(name = '🧹 Đã xóa')
  await ctx.send(embed = embed)
  
  
@bot.command(name = 'pause', aliases = ['stop', 'dừng'])
async def _pause(ctx):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
  if not p.voice_client.is_paused():
    p.voice_client.pause()
    await ctx.message.add_reaction('⏸️')

    
@bot.command(name = 'resume', aliases = ['continue', 'tiếp'])
async def _resume(ctx):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
  if p.voice_client.is_paused():
    p.voice_client.resume()
    await ctx.message.add_reaction('▶️')

    
@bot.command(name = 'loop', aliases = ['repeat', 'r', 'lặp'])
async def _loop(ctx, *, param = None):
  p = get_player(ctx.author.guild.id)
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
    param = param.lower()
    if param in ['0', 'off', 'tắt']:
      p.loop = 0
    elif param in ['1', 'single', 'one', 'một']:
      p.loop = 1
    elif param in ['2', 'all', 'queue', 'tất cả']:
      p.loop = 2
    else:
      embed = Embed(
        title = 'Sai cú pháp.',
        description = 'Hợp lệ: \n↩️ 0/tắt\n🔂 1/một\n🔁 2/tất cả',
        color = random_color()
      )
      embed.set_author(name = '❗ Lỗi')
      await ctx.send(embed = embed)
      return
  rc = '↩️'
  if p.loop == 1:
    rc = '🔂'
  if p.loop == 2:
    rc = '🔁'
  await ctx.message.add_reaction(rc)
  
  
@bot.command(name = 'shuffle', aliases = ['trộn'])
async def _shuffle(ctx):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'Không có bài nào.',
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
    
@bot.command(name = 'save', aliases = ['lưu'])
@commands.cooldown(1, 3, commands.BucketType.guild)
async def _save(ctx, *, pref = None):
  p = get_player(ctx.author.guild.id)
  if not p:
    return
  
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'Không có bài nào.',
      color = random_color()
    )
    await ctx.send(embed = embed)
    return
  
  if (pref == None) or (pref == ''):
    embed = Embed(
      title = 'Gõ tên danh mục phát bạn đã lưu.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  
  res, prefs = await resource_load('prefs.json')
  if not res:
    embed = Embed(
      title = prefs,
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  pref = str(pref)
  key = str(ctx.author.id)
  if key not in prefs:
    prefs[key] = {}
  prefs[key][pref] = []
  for song in p.songs:
    prefs[key][pref].append(song.to_dict())
  await resource_save('prefs.json', prefs)
  await ctx.message.add_reaction('📄')
  
@bot.command(name = 'load', aliases = ['tải'])
@commands.cooldown(1, 3, commands.BucketType.guild)
async def _load(ctx, *, pref = None):
  if is_restarting():
    embed = Embed(
      title = 'Đợi 2 phút bạn, bot đang restart.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  if not ctx.voice_client:
    if ctx.author.voice:
      await ctx.author.voice.channel.connect()
    else:
      embed = Embed(
        title = 'Vào voice đi bạn.',
        color = random_color()
      )
      embed.set_author(name = '❗ Lỗi')
      await ctx.send(embed = embed)
      return
  p = get_player(ctx.author.guild.id)
  if not p:
    embed = Embed(
      title = 'Lỗi rồi, cho bot thoát ra vào lại voice đi bạn.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  res, prefs = await resource_load('prefs.json')
  if not res:
    embed = Embed(
      title = prefs,
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  pref = str(pref)
  key = str(ctx.author.id)


  if key not in prefs:
    embed = Embed(
      title = 'Bạn chưa lưu gì cả.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  if (pref == 'None') or (pref == '') or (pref not in prefs[key]):
    embed = Embed(
      title = f'Không tìm thấy: {pref}',
      description = f'Danh mục phát bạn đã lưu:\n{", ".join(prefs[key].keys())}',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  songs = []
  async with ctx.typing():
    for song_dic in prefs[key][pref]:
      songs.append(Song.from_dict(song_dic))
    
  embed = Embed(
    title = f'🎵 {len(songs)} songs from 📄 {pref} 👤 {ctx.author.display_name}',
    color = random_color()
  )
  embed.set_author(name = '⏏️ Đang chờ phát')
  embed.set_footer(text = f'{len(p.songs)+1}/{len(p.songs)+len(songs)}')
  await ctx.send(embed = embed)
  p.text_channel = ctx.channel
  p.songs += songs
  
  
@bot.command(name = 'forget', aliases = ['quên'])
@commands.cooldown(1, 3, commands.BucketType.guild)
async def _forget(ctx, *, pref = None):
  res, prefs = await resource_load('prefs.json')
  if not res:
    embed = Embed(
      title = prefs,
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  pref = str(pref)
  key = str(ctx.author.id)
  if key not in prefs:
    embed = Embed(
      title = 'Bạn chưa lưu gì cả.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  if (pref == 'None') or (pref == '') or (pref not in prefs[key]):
    embed = Embed(
      title = f'Không tìm thấy: {pref}',
      description = f'Danh mục phát bạn đã lưu:\n{", ".join(prefs[key].keys())}',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  prefs[key].pop(pref, None)
  await resource_save('prefs.json', prefs)
  await ctx.message.add_reaction('📄')
    
    
bot.run(getenv('token'))
