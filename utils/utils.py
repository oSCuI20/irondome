# -*- coding: utf-8 -*-
#
# ./utils/utils.py
# Eduardo Banderas Alba
# 2022-08
#
# Aux functions
#
import os, sys, json
import hashlib


from math             import log2
from importlib        import import_module
from importlib.util   import find_spec


def tohex(b):
  return f'{b:02x}'
#tohex


def load_module(path, module_name):
  return getattr(import_module(path), module)
#load_module


def fp_write(content, filepath):
  with open(filepath, 'w') as fw:
    fw.write(content)
#fp_write


def explore(path, directory=False):
  if os.path.isfile(path):
    yield path

  for root, dirs, files in os.walk(path):
    for d in dirs:
      if directory:
        yield os.path.join(root, d)

    for f in files:
      if not directory:
        yield os.path.join(root, f)
#explore


def shannon_entropy(f):
  if not os.path.isfile(f):
    return 0.0

  entropy = 0.0
  total   = 0.0
  freq    = [ 0 * _ for _ in range(256 )]

  with open(f, 'rb') as fr:
    while True:
      b = fr.read(1)
      if not b:
        break

      freq[ord(b)] += 1
    #endwhile

    total = fr.tell()
  #endwith

  if total > 0:
    while len(freq) > 0:
      s = freq.pop(0)
      if s == 0:
        continue

      prob = s / total
      entropy += prob * log2(prob)
    #endwhile
  #endif

  return round(-entropy, 2)
#shannon_entropy


class ToObject:

  def __init__(self, **kwargs):
    for key, value in kwargs.items():
      self.__setattr__(key, value)

  def __repr__(self):
    return repr(self.__dict__)
#ToObject
