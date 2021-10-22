from random import randint
from datetime import datetime

from discord import Color
from pytz import timezone

def to_int(obj):
  try:
    return True, int(obj)
  except:
    return False, obj

def now():
  return datetime.now(timezone("Asia/Ho_Chi_Minh"))

def now_str():
  return now().strftime('%H:%M - %A, %B %d, %Y ')
  
def random_color():
  return Color.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))


class Page():
  pages = []
  
  @staticmethod
  def get_page(id):
    for p in Page.pages:
      if p.message.id == id:
        return p
    return None

  def __init__(self, message = None, value = 1):
    self.message = message
    self.value = value

  def increase(self, max_page):
    self.value += 1
    if self.value > max_page:
      self.value = max_page

  def decrease(self, max_page):
    self.value -= 1
    if self.value < 1:
      self.value = 1
