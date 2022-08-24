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

from importlib        import import_module
from importlib.util   import find_spec


def tohex(b):
  return f'{b:02x}'
#tohex


def load_module(path, module_name):
  return getattr(import_module(path), module)
#load_module


def checksum(content, algo=hashlib.sha256):
  return algo(content).hexdigest()
#checksum


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

class ToObject:

  def __init__(self, **kwargs):
    for key, value in kwargs.items():
      self.__setattr__(key, value)

  def __repr__(self):
    return repr(self.__dict__)
#ToObject
