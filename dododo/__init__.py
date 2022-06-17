from os import getenv
from random import shuffle

from discord.ext import commands
from discord import User, Embed, Intents, Activity, ActivityType
from dislash import InteractionClient, SelectMenu, SelectOption, ActionRow, Button, ButtonStyle
from asyncio import sleep
from traceback import format_exc as exc, format_tb

from dododo.song import Song
from dododo.player import prepare as player_prepare, Player
from dododo.youtube import search as youtube_search, download_info, download_info_playlist
from dododo.resource import prepare as resource_prepare, load as resource_load, save as resource_save
from dododo.system import TOKEN, prepare as system_prepare, log
from dododo.util import to_int, random_color, Page


bot = commands.Bot(command_prefix = ['#', '$', '-'], case_insensitive = True, intents = Intents.all())
bot.remove_command('help')
inter_bot = InteractionClient(bot)


@bot.event
async def on_ready():
  await bot.wait_until_ready()
  await bot.change_presence(
    activity = Activity(
      type = ActivityType.listening, 
      name = 'Watame Lullaby'
    )
  )
  await system_prepare(bot)
  await resource_prepare(bot)
  await player_prepare(bot)


@bot.event
async def on_error(event, *args, **kwargs):
  msg = f'Error in: {event}\n{exc()}'
  await log(msg)
  print(msg)


@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandNotFound):
    embed = Embed(
      title = 'Không tìm thấy lệnh.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
  elif isinstance(error, commands.CommandOnCooldown):
    embed = Embed(
      title = f'Thử lại sau {error.retry_after:.2f} giây.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
  else:
    msg = f'{error}'
    await log(msg)
    print(msg)

  
@bot.event
async def on_voice_state_update(member, before, after):
  if member.id == bot.user.id:
    if not before.channel and after.channel:
      for voice_client in bot.voice_clients:
        if voice_client.channel.id == after.channel.id:
          Player.players.append(Player(voice_client))
    if before.channel and not after.channel:
      p = Player.get_player(before.channel.id)
      if p:
        Player.players.remove(p)
  for p in Player.get_players():
    p.member = len(p.voice_client.channel.members)


@bot.command(name = 'help', aliases = ['h', 'giúp', 'giup'])
async def _help(ctx):
  def create_embed(page):
    embed = Embed(
      title = f'📄 {page}/{4}',
      color = random_color()
    )
    if page == 1:
      embed.add_field(name = '#️⃣ giúp', value = '📄 Xem các lệnh.\n*hoặc: giup, help, h*', inline = False)
      embed.add_field(name = '#️⃣ vào', value = '✅ Vào voice.\n*hoặc: vao, join, j*', inline = False)
      embed.add_field(name = '#️⃣ thoát', value = '❎ Thoát voice.\n*hoặc: thoat, leave, l*', inline = False)
      embed.add_field(name = '#️⃣ phát <link/từ khoá>', value = '⏏️ Phát bài hát từ link hoặc từ khoá.\n*hoặc: phat, play, p*', inline = False)
      embed.add_field(name = '#️⃣ tìm <từ khoá>', value = '🔎 Tìm bài hát, chọn để phát nhạc.\n*hoặc: tim, search, find, s, f*', inline = False)
    elif page == 2:  
      embed.add_field(name = '#️⃣ chờ', value = '📄 Xem danh sách bài chờ phát.\n*hoặc: cho, queue, playlist, q*', inline = False)
      embed.add_field(name = '#️⃣ đang', value = 'ℹ️ Xem bài đang phát.\n*hoặc: dang, now, current, info, c, i*', inline = False) 
      embed.add_field(name = '#️⃣ lùi', value = '⏮️ Phát bài trước đó.\n*hoặc: lui, back, bacc, previous, prev*', inline = False)
      embed.add_field(name = '#️⃣ tới', value = '⏭️ Phát bài tiếp theo.\n*hoặc: toi, next, skip*', inline = False)
      embed.add_field(name = '#️⃣ nhảy <vị trí>', value = '⤵️ Nhảy tới bài được chọn và phát.\n*hoặc: nhay, jump, move*', inline = False)
      embed.add_field(name = '#️⃣ xóa <vị trí>', value = '🧹 Xóa bài được chọn.\n*hoặc: xoá, xoa, remove, delete*', inline = False)
    elif page == 3:  
      embed.add_field(name = '#️⃣ dừng', value = '⏸️ Tạm dừng phát nhạc.\n*hoặc: dung, pause, stop*', inline = False)
      embed.add_field(name = '#️⃣ tiếp', value = '▶️ Tiếp tục phát nhạc.\n*hoặc: tiep, resume, continue*', inline = False)
      embed.add_field(name = '#️⃣ trộn', value = '🔀 Trộn danh mục phát và phát lại từ đầu.\n*hoặc: tron, shuffle*', inline = False)
      embed.add_field(name = '#️⃣ nghỉ', value = '⏹️ Dừng và xóa tất cả bài hát.\n*hoặc: nghi, clear, clean*', inline = False)
      embed.add_field(name = '#️⃣ lặp [chế độ]', value = '🔁 Chọn chế độ lặp: tắt/một/tất cả.\n*hoặc: lap, loop, repeat*', inline = False)
    else:
      embed.add_field(name = '#️⃣ lưu <tên danh sách phát>', value = '📄 Lưu danh sách phát.\n*hoặc: luu, save*', inline = False)
      embed.add_field(name = '#️⃣ tải <tên danh sách phát>', value = '📄 Tải danh sách phát đã lưu.\n*hoặc: tai, load*', inline = False)
      embed.add_field(name = '#️⃣ bỏ <tên danh sách phát>', value = '📄 Xoá danh sách phát đã lưu.\n*hoặc: bo, forget*', inline = False)
      embed.add_field(name = '#️⃣ chép <thành viên> <tên danh sách phát>', value = '📄 Ăn cắp danh sách phát của người khác.\n*hoặc: chep, copy*', inline = False)
    return embed
  
  page = Page(
    message = await ctx.send(
      embed = create_embed(1), 
      components = [
        ActionRow(
        Button(
          style = ButtonStyle.grey,
          label = '◀️',
          custom_id = 'left_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '▶️',
          custom_id = 'right_button'
          )
        )
      ]
    ),
    value = 1
  )
  Page.pages.append(page)
  on_click = page.message.create_click_listener(timeout = 300)

  @on_click.matching_id('left_button')
  async def on_left_button(inter):
    await inter.reply('Đợi xíu...', delete_after = 0)
    page = Page.get_page(inter.message.id)
    page.decrease(max_page = 4)
    await inter.message.edit(embed = create_embed(page.value))
    
  @on_click.matching_id('right_button')
  async def on_right_button(inter):
    await inter.reply('Đợi xíu...', delete_after = 0)
    page = Page.get_page(inter.message.id)
    page.increase(max_page = 4)
    await inter.message.edit(embed = create_embed(page.value))
    
  @on_click.timeout
  async def on_timeout():
    Page.pages.remove(page)
    await page.message.edit(components=[])


@bot.command(name = 'join', aliases = ['j', 'vào', 'vao'])
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
  
  
@bot.command(name = 'leave', aliases = ['l', 'thoát', 'thoat'])
async def _leave(ctx):
  for voice_client in bot.voice_clients:
    if voice_client.guild.id == ctx.author.guild.id:
      await voice_client.disconnect()
      await ctx.message.add_reaction('❎')

      
@bot.command(name = 'search', aliases = ['s', 'find', 'f', 'tìm', 'tim'])
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
      if len(options) >= 8:
        break
      res, song = await download_info(url)
      if res:
        options.append(SelectOption(label = f'🎵 {song.fixed_title(90)}', value = url, description = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(90)}'))
  
  components = [
    SelectMenu(
      custom_id = 'search',
      placeholder = 'Chọn bài ngay đây',
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

  
@bot.command(name = 'play', aliases = ['p', 'phát', 'phat'])
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
    
  p = Player.get_player(ctx.author.guild.id)
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
  playlist = None
  async with ctx.typing():
    if ('youtu.be' in text) or ('youtube.com' in text):
      if 'playlist?' in text:
        res, songs, playlist = await download_info_playlist(text)
        if not res:
          embed = Embed(
            title = songs,
            color = random_color()
          )
          embed.set_author(name = '❗ Lỗi')
          await ctx.send(embed = embed)
          return
      else:
        res, songs = await download_info(text)
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
        res, songs = await download_info(urls[0])
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
      title = f'🎵 {songs[0].fixed_title(97)}',
      description = f'🕒 {songs[0].fixed_duration()} 👤 {songs[0].fixed_uploader(97)}',
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
      title = f'🎵 {len(songs)} bài trong 📄 {playlist.fixed_title()} 👤 {playlist.fixed_uploader()}',
      url = playlist.url,
      color = random_color()
    )
    embed.set_thumbnail(url = playlist.thumbnail)
    embed.set_author(name = '⏏️ Đang chờ phát')
    embed.set_footer(text = f'#️⃣ {len(p.songs)+1}/{len(p.songs)+len(songs)}')
    await ctx.send(embed = embed)
  p.text_channel = ctx.channel
  p.songs += songs


@bot.command(name = 'back', aliases = ['prev', 'previous', 'bacc', 'lùi', 'lui'])
async def _back(ctx, response = True):
  p = Player.get_player(ctx.author.guild.id)
  if not p:
    return
  
  if p.voice_client.is_playing():
    if p.current - 2 < -1:
      p.current = -1
    else:
      p.current -= 2
    p.voice_client.stop()
  if response:
    await ctx.message.add_reaction('⏮')

  
@bot.command(name = 'skip', aliases = ['next', 'tới', 'toi'])
async def _skip(ctx, response = True):
  p = Player.get_player(ctx.author.guild.id)
  if not p:
    return
  
  if p.voice_client.is_playing():
    p.voice_client.stop()
  if response:
    await ctx.message.add_reaction('⏭️')
    

@bot.command(name = 'current', aliases = ['c', 'now', 'info', 'i', 'đang', 'dang'])
async def _current(ctx):
  def create_embed(p):
    if len(p.songs) <= 0:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      return embed

    song = p.songs[p.current]
    temp = Song(duration = p.played)
    if temp.duration > song.duration:
      temp.duration = song.duration
    embed = Embed(
      title = f'🎵 {song.fixed_title(97)}',
      description = f'🕒 {temp.fixed_duration()} / {song.fixed_duration()} 👤 {song.fixed_uploader(97)}\n\n📅 {song.fixed_upload_date()} 📈 {song.fixed_view_count()} 👍 {song.fixed_like_count()}\n\n{song.fixed_description()}',
      url = f'{song.url}&start={temp.duration}',
      color = random_color()
    )
    if song.thumbnail:
      embed.set_thumbnail(url = song.thumbnail)
    embed.set_author(name = '▶️ Đang phát')
    embed.set_footer(text = f'#️⃣ {p.current+1}/{len(p.songs)}')
    return embed

  p = Player.get_player(ctx.author.guild.id)
  if not p:
    return

  message = await ctx.send(
    embed = create_embed(p), 
    components = [
      ActionRow(
        Button(
          style = ButtonStyle.grey,
          label = '⏮️',
          custom_id = 'previous_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '⏸️',
          custom_id = 'pause_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '▶️',
          custom_id = 'resume_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '🧹',
          custom_id = 'remove_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '⏭️',
          custom_id = 'next_button'
        )
      )
    ]
  )
  on_click = message.create_click_listener(timeout = 300)

  @on_click.matching_id('previous_button')
  async def on_left_button(inter):
    p = Player.get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return

    sec = 3
    await inter.reply('Đợi tý...', delete_after = sec)
    await _back(inter, response = False)
    await sleep(sec)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])
    
  @on_click.matching_id('next_button')
  async def on_right_button(inter):
    p = Player.get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return 

    sec = 3
    await inter.reply('Đợi tý...', delete_after = sec)
    await _skip(inter, response = False)
    await sleep(sec)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])

  @on_click.matching_id('pause_button')
  async def on_pause_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    p = Player.get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return

    await _pause(inter, response = False)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])

  @on_click.matching_id('resume_button')
  async def on_resume_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    p = Player.get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return

    await _resume(inter, response = False)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])
    
  @on_click.matching_id('remove_button')
  async def on_remove_button(inter):
    p = Player.get_player(inter.author.guild.id)
    if not p:
      await inter.message.delete()
      return
    
    sec = 3
    await inter.reply('Đợi tý...', delete_after = sec)
    await _remove(inter, p.current+1)
    await sleep(sec)
    await inter.message.edit(embed = create_embed(p))
    if inter.message.embeds[0].title.startswith('Không có bài nào.'):
      await inter.message.edit(components=[])

  @on_click.timeout
  async def on_timeout():
    await message.edit(components=[])


@bot.command(name = 'jump', aliases = ['move', 'nhảy', 'nhay'])
async def _jump(ctx, param = None):
  p = Player.get_player(ctx.author.guild.id)
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
      title = f'"{i}" không phải là số hay vị trí.',
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
      
     
@bot.command(name = 'queue', aliases = ['q', 'playlist', 'all', 'chờ', 'cho'])
async def _queue(ctx):
  def create_embed(current_page, max_page): 
    embed = Embed(
      title = f'📄 {current_page} / {max_page}',
      color = random_color()
    )
    value = ''
    for i in range(0, 5):
      index = (current_page-1) * 5 + i
      if index < len(p.songs):
        song = p.songs[index]
        if index == p.current:
          embed.add_field(name = f'▶️ {index+1} 🎵 *{song.fixed_title(97)}*', value = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(97)}\n└Đang phát────────────────', inline = False)
        else:
          embed.add_field(name = f'#️⃣ {index+1} 🎵 {song.fixed_title(97)}', value = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(97)}', inline = False)
    duration = 0
    for song in p.songs:
      duration += song.duration
    text = f'#️⃣ {len(p.songs)} bài 🕒 {Song(duration = duration).fixed_duration()}'
    loop = '↩️ tắt'
    if p.loop == 1:
      loop = '🔂 một'
    if p.loop == 2:
      loop = '🔁 tất cả'
    text = loop + ' ' + text   
    embed.set_footer(text = text)
    return embed

  def create_components(loop):
    label = '↩️'
    if loop == 1:
      label = '🔂'
    if loop == 2:
      label = '🔁'
    return [
      ActionRow(
        Button(
          style = ButtonStyle.grey,
          label = '⏪',
          custom_id = 'left_button_5'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '◀️',
          custom_id = 'left_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '▶️',
          custom_id = 'right_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '⏩',
          custom_id = 'right_button_5'
        )
      ),
      ActionRow(
        Button(
          style = ButtonStyle.grey,
          label = label,
          custom_id = 'loop_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '🔀',
          custom_id = 'shuffle_button'
        ),
        Button(
          style = ButtonStyle.grey,
          label = '⏹️',
          custom_id = 'clear_button'
        )
      )
    ]

  p = Player.get_player(ctx.author.guild.id)
  if not p:
    return
  if len(p.songs) <= 0:
    embed = Embed(
      title = 'Không có bài nào.',
      color = random_color()
    )
    await ctx.send(embed = embed)
    return
  

  current_page = p.current // 5 + 1
  max_page = (len(p.songs)-1) // 5 + 1
  
  page = Page(
    message = await ctx.send(
      embed = create_embed(current_page, max_page),
      components = create_components(p.loop)
    ),
    value = current_page
  )
  Page.pages.append(page)
  on_click = page.message.create_click_listener(timeout = 300)

  @on_click.matching_id('left_button')
  async def on_left_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      max_page = (len(p.songs)-1) // 5 + 1
      page = Page.get_page(inter.message.id)
      page.decrease(max_page)
      await inter.message.edit(embed = create_embed(page.value, max_page))
    else:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      page = Page.get_page(inter.message.id)
      if page:
        Page.pages.remove(page)
      await inter.message.edit(embed = embed, components = [])

  @on_click.matching_id('right_button')
  async def on_right_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      max_page = (len(p.songs)-1) // 5 + 1
      page = Page.get_page(inter.message.id)
      page.increase(max_page)
      await inter.message.edit(embed = create_embed(page.value, max_page))
    else:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      page = Page.get_page(inter.message.id)
      if page:
        Page.pages.remove(page)
      await inter.message.edit(embed = embed, components = [])

  @on_click.matching_id('left_button_5')
  async def on_left_button_5(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      max_page = (len(p.songs)-1) // 5 + 1
      page = Page.get_page(inter.message.id)
      page.decrease(max_page, 5)
      await inter.message.edit(embed = create_embed(page.value, max_page))
    else:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      page = Page.get_page(inter.message.id)
      if page:
        Page.pages.remove(page)
      await inter.message.edit(embed = embed, components = [])
  
  @on_click.matching_id('right_button_5')
  async def on_right_button_5(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      max_page = (len(p.songs)-1) // 5 + 1
      page = Page.get_page(inter.message.id)
      page.increase(max_page, 5)
      await inter.message.edit(embed = create_embed(page.value, max_page))
    else:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      page = Page.get_page(inter.message.id)
      if page:
        Page.pages.remove(page)
      await inter.message.edit(embed = embed, components = [])

  @on_click.matching_id('loop_button')
  async def on_loop_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      max_page = (len(p.songs)-1) // 5 + 1
      page = Page.get_page(inter.message.id)
      await _loop(inter, param = None, response = False)
      await inter.message.edit(embed = create_embed(page.value, max_page), components = create_components(p.loop))
    else:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      page = Page.get_page(inter.message.id)
      if page:
        Page.pages.remove(page)
      await inter.message.edit(embed = embed, components = [])

  @on_click.matching_id('shuffle_button')
  async def on_shuffle_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      await _shuffle(inter, response = False)
      page = Page.get_page(inter.message.id)
      page.set(1)
      await inter.message.edit(embed = create_embed(page.value, max_page))
    else:
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      page = Page.get_page(inter.message.id)
      if page:
        Page.pages.remove(page)
      await inter.message.edit(embed = embed, components = [])

  @on_click.matching_id('clear_button')
  async def on_clear_button(inter):
    await inter.reply('Đợi tý...', delete_after = 0)
    if len(p.songs) > 0:
      await _clear(inter, response = False)
      embed = Embed(
        title = 'Không có bài nào.',
        color = random_color()
      )
      page = Page.get_page(inter.message.id)
      if page:
        Page.pages.remove(page)
      await inter.message.edit(embed = embed, components = [])

  @on_click.timeout
  async def on_timeout():
    Page.pages.remove(page)
    await page.message.edit(components=[])


@bot.command(name = 'clear', aliases = ['clean', 'nghỉ', 'nghi'])
async def _clear(ctx, response = True):
  p = Player.get_player(ctx.author.guild.id)
  if not p:
    return
  
  if len(p.songs) > 0:
    p.songs.clear()
  if p.voice_client.is_playing():
    p.voice_client.stop()
  p.current = 0
  if response:
    await ctx.message.add_reaction('⏹️')
  

@bot.command(name = 'remove', aliases = ['delete', 'xóa', 'xoá', 'xoa'])
async def _remove(ctx, param = None):
  p = Player.get_player(ctx.author.guild.id)
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
      title = f'"{i}" không phải là số hay vị trí.',
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
    title = f'🎵 {song.fixed_title(97)}',
    description = f'🕒 {song.fixed_duration()} 👤 {song.fixed_uploader(97)}',
    url = song.url,
    color = random_color()
  )
  if song.thumbnail:
    embed.set_thumbnail(url = song.thumbnail)
  embed.set_author(name = '🧹 Đã xóa')
  await ctx.send(embed = embed)
  
  
@bot.command(name = 'pause', aliases = ['stop', 'dừng', 'dung'])
async def _pause(ctx, response = True):
  p = Player.get_player(ctx.author.guild.id)
  if not p:
    return
  if not p.voice_client.is_paused():
    p.voice_client.pause()
  if response:
    await ctx.message.add_reaction('⏸️')

    
@bot.command(name = 'resume', aliases = ['continue', 'tiếp', 'tiep'])
async def _resume(ctx, response = True):
  p = Player.get_player(ctx.author.guild.id)
  if not p:
    return
  if p.voice_client.is_paused():
    p.voice_client.resume()
  if response:
    await ctx.message.add_reaction('▶️')

    
@bot.command(name = 'loop', aliases = ['repeat', 'lặp', 'lap'])
async def _loop(ctx, *, param = None, response = True):
  p = Player.get_player(ctx.author.guild.id)
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
    if param in ['0', 'off', 'tắt', 'tat']:
      p.loop = 0
    elif param in ['1', 'single', 'one', 'một', 'mot']:
      p.loop = 1
    elif param in ['2', 'all', 'queue', 'tất cả', 'tat ca']:
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
  if response:
    await ctx.message.add_reaction(rc)
  
  
@bot.command(name = 'shuffle', aliases = ['trộn', 'tron'])
async def _shuffle(ctx, response = True):
  p = Player.get_player(ctx.author.guild.id)
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
  if response:
    await ctx.message.add_reaction('🔀')
    
    
@bot.command(name = 'save', aliases = ['lưu', 'luu'])
@commands.cooldown(1, 3, commands.BucketType.guild)
async def _save(ctx, *, pref = None):
  p = Player.get_player(ctx.author.guild.id)
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

  res, msg = await resource_save('prefs.json', prefs)
  if not res:
    embed = Embed(
      title = msg,
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  await ctx.message.add_reaction('📄')
  
  
@bot.command(name = 'load', aliases = ['tải', 'tai'])
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
      
  p = Player.get_player(ctx.author.guild.id)
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
    title = f'🎵 {len(songs)} bài trong 📄 {pref} 👤 {ctx.author.display_name}',
    color = random_color()
  )
  embed.set_author(name = '⏏️ Đang chờ phát')
  embed.set_footer(text = f'{len(p.songs)+1}/{len(p.songs)+len(songs)}')
  await ctx.send(embed = embed)
  p.text_channel = ctx.channel
  p.songs += songs
  
  
@bot.command(name = 'forget', aliases = ['bỏ', 'bo'])
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
  
  res, msg = await resource_save('prefs.json', prefs)
  if not res:
    embed = Embed(
      title = msg,
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  await ctx.message.add_reaction('📄')
    

@bot.command(name = 'copy', aliases = ['chép', 'chep'])
@commands.cooldown(1, 3, commands.BucketType.guild)
async def _copy(ctx, user: User, *, pref = None):
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
  key = str(user.id)

  if key not in prefs:
    embed = Embed(
      title = f'{user.display_name} chưa lưu gì cả.',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return
  
  if (pref == 'None') or (pref == '') or (pref not in prefs[key]):
    embed = Embed(
      title = f'Không tìm thấy: {pref}',
      description = f'Danh mục phát {user.display_name} đã lưu:\n{", ".join(prefs[key].keys())}',
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  prefs[str(ctx.author.id)][pref] = prefs[key][pref]
    
  res, msg = await resource_save('prefs.json', prefs)
  if not res:
    embed = Embed(
      title = msg,
      color = random_color()
    )
    embed.set_author(name = '❗ Lỗi')
    await ctx.send(embed = embed)
    return

  await ctx.message.add_reaction('📄')

    
bot.run(TOKEN)
