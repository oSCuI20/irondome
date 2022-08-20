# -*- coding: utf-8 -*-
#
# ./irondome.py
# Eduardo Banderas Alba
# 2022-08
#
# Detección de actividad anómala
#
"""
  {0} [OPTIONS] <path> <file-extension>

  OPTIONS:
    -event values separate for comas, default all. Valid values:
        'access'
        'modify'
        'attrib'
        'create'
        'delete'
        'delete self'
        'move from'
        'move to'
        'open'
        'closed'
        'closed'
    -help
"""
import sys, os

from time import time, sleep, strftime, localtime

from fs.inotify   import IEvent
from fs.monitor   import FSWatcher
from utils.utils  import *


class args:
  logfile  = '/var/log/irondome/irondome.logs'
  basepath = os.path.dirname(os.path.abspath(sys.argv[0]))

  watchpath  = None
  extensions = []
  maxmemory  = 100 # MB

  events = [
    'access',
    'modify',
    'attrib',
    'create',
    'delete',
    'delete self',
    'move from',
    'move to',
    'open',
    'closed',
    'closed',
  ]
#class args


def main():
  parse_arguments()

  watchers = FSWatcher(args.extensions)
  flags    = IEvent.get_flags(IEvent, args.events)

  watchers.add_event(path=args.watchpath, flags=flags)

  while True:
    for event in watchers.read_events():
      print(f'{strftime("%Y-%m-%d %H:%M:%S ", localtime())} -- {event}')

    sleep(0.2)
  #endwhile
#main

def parse_arguments():
  options_ = [ '-event', '-help' ]
  options  = ' '.join(sys.argv[1:]).strip().split(' ')

  events = []
  i = 0
  while len(options)  > i:
    data = options[i]
    if data == '-events':
      i += 1
      events = options[i].split(',')
    elif data == '-help':
      halt_with_doc('', __doc__, sys.argv[0], 0)

    else:
      args.watchpath = os.path.abspath(options[i])
      i += 1
      if len(options) > i:
        args.extensions = options[i:]
        i += 1 + len(args.extensions)
      #endif

      continue

    i += 1
  #endwhile

  print(args.__dict__)
  if not args.watchpath:
    halt('ERROR: set directory to monitoring')

  if not os.path.exists(args.watchpath):
    halt('ERROR: path not found')

  for event in events:
    if event not in args.events:
      halt(f'ERROR: {event} not recognized')
  #endfor

  if len(events) > 0:
    args.events = events
#parse_arguments


if __name__ == "__main__":
  try:    reload(sys); sys.setdefaultencoding("utf8")
  except: pass

  if os.getuid() != 0:
    halt('ERROR: You need root privileges', 1)

  main()
