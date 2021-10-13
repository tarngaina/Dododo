from urllib import parse, request
from asyncio import get_event_loop
from traceback import format_exc as exc
from re import compile, findall

from discord import PCMVolumeTransformer, FFmpegOpusAudio
from yt_dlp import YoutubeDL

from song import Song
from maintenance import restart, log
from util import strip_ansi

def search(text, limit = 25):
  ids = None
  try:
    ids = findall(r'/watch\?v=(.{11})',  request.urlopen('http://www.youtube.com/results?' +  parse.urlencode({'search_query': text})).read().decode())
  
  except Exception as e:
    msg = f'{e}\n{exc()}'
    get_event_loop().create_task(log(msg))
    return False, str(e)
  
  else:
    if (not ids) or (len(ids) == 0):
      return False, f'No song found with: {text}.'

    urls = []
    for id in ids:
      url = f'https://youtu.be/{id}'
      if url not in urls:
        urls.append(url)
    if len(urls) > limit:
      urls = urls[:limit]
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
    'verbose':True
  }
)

async def get_info(url):
  data = None
  try:
    url = r'https://youtu.be/' + url.split('=')[1][:11] if 'list=' in url else url
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_extract.extract_info(url, download=False))
  
  except Exception as e:
    msg = f'{strip_ansi(e)}\n{exc()}'
    await log(msg)
    return False, strip_ansi(str(e))
  
  else: 
    entry = data
    song = Song(
      entry['title'],
      entry['uploader'],
      int(entry['duration']),
      r'https://youtu.be/' + entry['id'],
      thumbnail = entry['thumbnail']
    )
    return True, song

async def get_info_playlist(url):
  data = None
  try:
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_extract.extract_info(url, download=False))
  
  except Exception as e:
    msg = f'{strip_ansi(e)}\n{exc()}'
    await log(msg)
    return False, strip_ansi(str(e))
  
  else:
    await log(str(data))
    songs = []
    for entry in data['entries']:
      songs.append(
        Song(
          entry['title'],
          entry['uploader'],
          int(entry['duration']),
          r'https://youtu.be/' + entry['id']
        )
      )
    return True, songs
    

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
    'verbose':True
  }
)


async def get_source(url, song = None):
  data = None
  try: 
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_source.extract_info(url, download=False))
  
  except Exception as e:
    msg = f'{strip_ansi(e)}\n{exc()}'
    await log(msg)
    return False, strip_ansi(str(e)), song
  
  else:
    if song:
      song.title = data['title']
      song.uploader = data['uploader']
      song.thumbnail = data['thumbnail']
    return True, FFmpegOpusAudio(data['url'], before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options = '-vn'), song
  
