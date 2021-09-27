from random import randint

from discord import Color

def to_int(obj):
  try:
    return True, int(obj)
  except:
    return False, obj
  
def to_float(obj):
  try:
    return True, float(obj)
  except:
    return False, obj
  
def random_color():
  return Color.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))