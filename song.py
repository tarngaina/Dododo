class Song:
  def __init__(self, **dic):
    if 'title' in dic:
      self.title = dic['title']
    if 'uploader' in dic:
      self.uploader = dic['uploader']
    if 'duration' in dic:
      self.duration = dic['duration']
    if 'url' in dic:
      self.url = dic['url']
    if 'thumbnail' in dic:
      self.thumbnail = dic['thumbnail']
    if 'upload_date' in dic:
      self.upload_date = dic['upload_date']
    if 'view_count' in dic:
      self.view_count = dic['view_count']
    if 'like_count' in dic:
      self.like_count = dic['like_count']

  @classmethod
  def from_dict(cls, dic):
    return cls(
      dic['title'],
      dic['uploader'],
      dic['duration'],
      dic['url']
    )

  def to_dict(self):
    return {
      'title': self.title,
      'uploader': self.uploader,
      'duration': self.duration,
      'url': self.url
    }

  def update(self, **dic):
    if 'title' in dic:
      self.title = dic['title']
    if 'uploader' in dic:
      self.uploader = dic['uploader']
    if 'duration' in dic:
      self.duration = dic['duration']
    if 'url' in dic:
      self.url = dic['url']
    if 'thumbnail' in dic:
      self.thumbnail = dic['thumbnail']
    if 'upload_date' in dic:
      self.upload_date = dic['upload_date']
    if 'view_count' in dic:
      self.view_count = dic['view_count']
    if 'like_count' in dic:
      self.like_count = dic['like_count']

  def fixed_duration(self):
    m, s = divmod(self.duration, 60)
    h, m = divmod(m, 60)
    if h > 0:
      return f'{h:02d}:{m:02d}:{s:02d}'
    else:
      return f'{m:02d}:{s:02d}'
  
  def fixed_title(self, limit = 80):
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
   
  def fixed_uploader(self, limit = 32):
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
      return f'🕒 {self.fixed_duration()} 🎵 {self.fixed_title()} 👤 {self.fixed_uploader()}';
    else:
      return f'🕒 {self.fixed_duration()} 🎵 {self.fixed_title(999)} 👤 {self.fixed_uploader(999)}';
