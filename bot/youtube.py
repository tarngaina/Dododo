from urllib import parse, request
from asyncio import get_event_loop
from traceback import format_exc as exc
from re import compile, findall

from discord import PCMVolumeTransformer, FFmpegPCMAudio
from yt_dlp import YoutubeDL

from bot.song import Song, Playlist
from bot.system import log


def search(query = None, limit = 10):
  if not query:
    return False, 'Không có từ khóa được nhập vào.'

  ids = None
  try:
    ids = findall(r'/watch\?v=(.{11})',  request.urlopen('http://www.youtube.com/results?' +  parse.urlencode({'search_query': query})).read().decode())
  
  except Exception as e:
    msg = f'{e}\n{exc()}'
    get_event_loop().create_task(log(msg))
    return False, str(e)
  
  else:
    if (not ids) or (len(ids) == 0):
      return False, f'Không tìm thấy bài hát với từ khóa: {query}.'

    
    ids = list(dict.fromkeys(ids))

    urls = []
    for id in ids:
      if (len(urls) >= limit):
        break
      urls.append(f'https://youtu.be/{id}')
    return True, urls
    

ytdl_extract = YoutubeDL(
  {
    'extract_flat': True, 
    'simulate': True,
    'skip_download': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': False,
    'no_warnings': True,
    'verbose':True,
    'ignore_no_formats_error':True,
    'no_color':True
  }
)

async def download_info(url = None):
  if not url:
    return False, 'Không có link nhập vào.'

  data = None
  try:
    url = r'https://youtu.be/' + url.split('=')[1][:11] if 'list=' in url else url
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_extract.extract_info(url, download=False))
  
  except Exception as e:
    msg = f'{e}\n{exc()}'
    await log(msg)
    return False, str(e)
  
  else: 
    if data:
      entry = data
      if ('duration' in entry) and (entry['duration']):
        song = Song(**entry)
        song.update(url = r'https://youtu.be/' + entry['id'])
        return True, song

    return False, f'Không tìm thấy bài hát với link {url}.'


async def download_info_playlist(url = None):
  if not url:
    return False, 'Không có link nhập vào.', None

  data = None
  try:
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_extract.extract_info(url, download=False))
  
  except Exception as e:
    msg = f'{e}\n{exc()}'
    await log(msg)
    return False, str(e), None
  
  else:
    playlist = None
    songs = []
    if data:
      if ('uploader' in data) and data['uploader']:
        playlist = Playlist(
          title = data['title'],
          uploader = data['uploader'],
          url = data['original_url'],
          thumbnail = data['thumbnails'][-1]['url'].split('?')[0]
        )
      if ('entries' in data) and (data['entries']):
        for entry in data['entries']:
          if ('duration' in entry) and (entry['duration']):
            song = Song(**entry)
            song.update(url = r'https://youtu.be/' + entry['id'])
            songs.append(song)
    return True, songs, playlist
    

ytdl_source = YoutubeDL(
  {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': False,
    'no_warnings': True,
    'verbose':True,
    'no_color':True
  }
)

async def download_audio_source(url = None, song = None):
  if not url and not song:
    return Fase, 'Không có link nhập vào.', song
  if song and not url:
    url = song.url

  data = None
  try: 
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_source.extract_info(url, download=False))
  
  except Exception as e:
    msg = f'{e}\n{exc()}'
    await log(msg)
    return False, str(e), song
  
  else:
    if data:
      song.update(
        title = data['title'], 
        uploader = data['uploader'], 
        thumbnail = data['thumbnail'],
        description = data['description'],
        like_count = data['like_count'],
        view_count = data['view_count'],
        upload_date = data['upload_date']
      )
      return True, PCMVolumeTransformer(FFmpegPCMAudio(data['url'], before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options = '-vn'), volume = 1.8), song
    return False, 'Lỗi gì rồi chiu.', song
