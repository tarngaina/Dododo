from discord import PCMVolumeTransformer, FFmpegOpusAudio
from youtube_dl import YoutubeDL
from song import Song
from urllib import parse, request
from asyncio import get_event_loop
from traceback import format_exc as exc
from re import compile, findall, search as src
import reminder

def search(text, limit = 25):
  try:
    ids = findall(r'/watch\?v=(.{11})',  request.urlopen('http://www.youtube.com/results?' +  parse.urlencode({'search_query': text})).read().decode())
    if not ids or (len(ids) == 0):
      return False, f'No song found with: {text}.'
    urls = []
    for id in ids:
      url = f'https://youtu.be/{id}'
      if url not in urls:
        urls.append(url)
    if len(urls) > limit:
      urls = urls[:limit]
    return True, urls
  except Exception as e:
    print(exc())
    return False, str(e)

ytdl_extract = YoutubeDL(
  {
    'extract_flat': True, 
    'ignoreerrors': True,
    'quiet': True,
    'simulate': True,
    'skip_download': True,
    'logtostderr':False,
    'no_warnings': True,
    'verbose':False,
    'source_address': '0.0.0.0'
  }
)

async def get_info(url):
  try:
    url = r'https://youtu.be/' + url.split('=')[1][:11] if 'list=' in url else url
    entry = await get_event_loop().run_in_executor(None, lambda: ytdl_extract.extract_info(url, download=False))
    if not entry:
      await reminder.send()
    song = Song(
      entry['title'],
      entry['uploader'],
      int(entry['duration']),
      r'https://youtu.be/' + entry['id'],
      thumbnail = entry['thumbnail']
    )
    return True, song
  except Exception as e:
    print(exc())
    return False, str(e)

async def get_info_playlist(url):
  try:
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_extract.extract_info(url, download=False))
    if not entry:
      await reminder.send()
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
  except Exception as e:
    print(exc())
    return False, str(e)
    

ytdl_source = YoutubeDL(
  {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'verbose':False,
    'source_address': '0.0.0.0'
  }
)


async def get_source(url, song = None):
  try: 
    data = await get_event_loop().run_in_executor(None, lambda: ytdl_source.extract_info(url, download=False))
    if not data:
      await reminder.send()
    if song:
      song.title = data['title']
      song.uploader = data['uploader']
      song.thumbnail = data['thumbnail']
    return True, FFmpegOpusAudio(data['url'], before_options = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options = '-vn'), song
  except Exception as e:
    print(exc())
    return False, str(e), song
  
