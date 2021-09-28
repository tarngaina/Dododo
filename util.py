from random import randint
from datetime import datetime
from re import compile, sub

from discord import Color
from pytz import timezone

def to_int(obj):
  try:
    return True, int(obj)
  except:
    return False, obj

def now():
  return datetime.now(timezone("Asia/Ho_Chi_Minh"))
  
def random_color():
  return Color.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))

def strip_ansi(text):
  return compile(r'\x1B\[\d+(;\d+){0,2}m').sub('', str(text))