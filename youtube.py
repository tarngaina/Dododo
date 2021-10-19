from urllib import parse, request
from asyncio import get_event_loop
from traceback import format_exc as exc
from re import compile, findall

from discord import PCMVolumeTransformer, FFmpegOpusAudio, FFmpegPCMAudio
from yt_dlp import YoutubeDL

from song import Song
from maintenance import restart, log
from util import strip_ansi

def search(text, limit = 24):
  ids = None
  try:
    ids = findall(r'/watch\?v=(.{11})',  request.urlopen('http://www.youtube.com/results?' +  parse.urlencode({'search_query': text})).read().decode())
  
  except Exception as e:
    msg = f'{e}\n{exc()}'
    get_event_loop().create_task(log(msg))
    return False, str(e)
  
  else:
    if (not ids) or (len(ids) == 0):
      return False, f'Không tìm thấy bài hát với từ khóa: {text}.'

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
    'verbose':True,
    'ignore_no_formats_error':True,
    'no_color':True
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
    if ('duration' in entry) and (entry['duration']):
      song = Song(**entry)
      song.update(url = r'https://youtu.be/' + entry['id'])
      return True, song
    return False, f'Không tìm thấy bài hát với link {url}.'


async def get_info_playlist(url):
  data = None
  try:
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_extract.extract_info(url, download=False))
  
  except Exception as e:
    msg = f'{strip_ansi(e)}\n{exc()}'
    await log(msg)
    return False, strip_ansi(str(e)), None
  
  else:
    infos = {}
    if 'title' in data:
      infos['title'] = data['title']
    if 'uploader' in data:
      infos['uploader'] = data['uploader']
    if 'original_url' in data:
      infos['url'] = data['original_url']
    if 'thumbnails' in data:
      if data['thumbnails'] != None:
        infos['thumbnail'] = data['thumbnails'][-1]['url'].split('?')[0]

    songs = []
    if ('entries' in data) and (data['entries']):
      for entry in data['entries']:
        if ('duration' in entry) and (entry['duration']):
          song = Song(**entry)
          song.update(url = r'https://youtu.be/' + entry['id'])
          songs.append(song)
    return True, songs, infos
    

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

async def get_source(url, song = None):
  data = None
  try: 
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_source.extract_info(url, download=False))
  
  except Exception as e:
    msg = f'{strip_ansi(e)}\n{exc()}'
    await log(msg)
    return False, strip_ansi(str(e)), song
  
  else:
    song.update(
      title = data['title'], 
      uploader = data['uploader'], 
      thumbnail = data['thumbnail'],
      description = data['description'],
      like_count = data['like_count'],
      view_count = data['view_count'],
      upload_date = data['upload_date']
    )
    return True, PCMVolumeTransformer(FFmpegPCMAudio(data['url'], before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options = '-vn'), volume = 1.75), song
  
