class Song:
  def __init__(self, title, uploader, duration, url, thumbnail = None):
    self.title = title
    self.uploader = uploader
    self.duration = duration
    self.url = url
    self.thumbnail = thumbnail

  def to_dic(self):
    return {
      'title': self.title,
      'uploader': self.uploader,
      'duration': self.duration,
      'url': self.url
    }

  def fixed_duration(self):
    m, s = divmod(self.duration, 60)
    h, m = divmod(m, 60)
    if h > 0:
      return f'{h:02d}:{m:02d}:{s:02d}'
    else:
      return f'{m:02d}:{s:02d}'
  
  def fixed_title(self, limit = 32):
    t = self.title
    t = ' '.join(t.split(' '))
    if t[0] == ' ':
      t = t[1:]
    if t[-1] == ' ':
      t = t[:-1]
    cs = ['|', '`', '*', '_', '>']
    for c in cs:
      t = t.replace(c, '')
    if len(t) > limit:
      t = t[:limit] + '...'
    return t
   
  def fixed_uploader(self, limit = 16):
    t = self.uploader
    t = ' '.join(t.split(' '))
    if t[0] == ' ':
      t = t[1:]
    if t[-1] == ' ':
      t = t[:-1]
    cs = ['|', '`', '*', '_', '>']
    for c in cs:
      t = t.replace(c, '')
    if len(t) > limit:
      t = t[:limit] + '...'
    return t
  
  def to_str(self, limit = True):
    if limit:
      return f'[{self.fixed_duration()}] {self.fixed_title()} - {self.fixed_uploader()}';
    else:
      return f'[{self.fixed_duration()}] {self.fixed_title(999)} - {self.fixed_uploader(999)}';

def from_dic(dic):
  return Song(
    dic['title'],
    dic['uploader'],
    dic['duration'],
    dic['url']
)
