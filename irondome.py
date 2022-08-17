# -*- coding: utf-8 -*-
#
# ./irondome.py
# Eduardo Banderas Alba
# 2022-08
#
# Detección de actividad anómala
#
"""
  {0} <path> <file-extension>
"""
import sys, os

from utils.utils           import *


class args:
  logfile  = '/var/log/irondome/irondome.logs'
  filepath = None
  filetype = None

  maxmemory = 100 # MB
#class args


def main():
  parse_arguments()

  return
#main


def parse_arguments():
  if len(sys.argv) == 1:
    halt_with_doc('', __doc__, sys.argv[0], 0)

  path  = sys.argv[1]
  types = sys.argv[2:]

  if not os.path.exists(path):
    halt('ERROR: path not found')

  args.filepath = path
  args.filetype = types
#parse_arguments


if __name__ == "__main__":
  try:    reload(sys); sys.setdefaultencoding("utf8")
  except: pass

  if os.getuid() != 0:
    halt('ERROR: You need root privileges', 1)

  main()
