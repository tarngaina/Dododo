from os import path, makedirs
from json import dump, load
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


def save_prefs(id, prefs):
  if len(prefs) > 0:
    with open(f'data/{id}.json', 'w+', encoding = 'utf-8') as f:
      dump(prefs, f, ensure_ascii = False, indent = 2)
    
def load_prefs(id):
  if path.exists(f'data/{id}.json'):
    with open(f'data/{id}.json', 'r', encoding = 'utf-8') as f:
      return load(f)
  else:
    with open(f'data/{id}.json', 'w+', encoding = 'utf-8') as f:
      dump({}, f, indent = 2)
    return {}

if not path.exists('data'):
  makedirs('data')
