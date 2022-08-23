# -*- coding: utf-8 -*-
#
# ./irondome.py
# Eduardo Banderas Alba
# 2022-08
#
# Detección de actividad anómala
#
"""
  {program} [OPTIONS] <path1,path2,...> <file-extension>

  OPTIONS:
    -events values separate for comas, default all. Valid values:
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
    -logfile default, {logfile}
    -help
"""
import sys, os

from time import time, sleep, strftime, localtime

from utils import Logger
from fs    import FSEvent, FSWatcher, FSWatcherError, FSIntegrity


class args:
  program  = sys.argv[0]
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
  ]
#class args


def main(logger):
  parse_arguments(logger)

  logger.debug(f'args {args.__dict__}')

  #TODO Load FSIntegrity
  logger.debug(f'running system integrity')
  integrity = []

  FSIntegrity(args.watchpath[0])
  # for path in args.watchpath:
  #   try:
  #     logger.debug(f'FS Integrity {path}')
  #     i = FSIntegrity(path)
  #
  #     integrity.append()
  #
  #   except:
  #     logger.error(f'{err}, {path}')
  #     logger.debug(f'{err}, {path}')
  #endfor

  #sys.exit(1)
  watchers = FSWatcher(args.extensions)
  flags    = FSEvent.get_flags(FSEvent, args.events)

  logger.debug(f'events {args.events} flags {bin(flags)}')
  notfound = []

  for path in args.watchpath:
    logger.debug(f'watcher into {path}')
    try:
      watchers.add_event(path=path, flags=flags)
    except FSWatcherError as err:
      logger.error(f'{err}, {path}')
      logger.debug(f'{path} not found')
      notfound.append(path)
  #forend

  if len(notfound) == len(args.watchpath):
    logger.halt(f'paths not found')

  while True:
    for event in watchers.read_events():
      print(f'{strftime("%Y-%m-%d %H:%M:%S ", localtime())} -- {event}')

    sleep(0.2)
  #endwhile
#main

def parse_arguments(logger):
  options_ = [ '-event', '-logfile', '-help' ]
  options  = sys.argv[1:]

  events = []
  if len(options) <= 0:
    logger.halt_with_doc('', __doc__.format(program=args.program,
                                            logfile=args.logfile))

  while len(options) > 0:
    data = options.pop(0)
    if data in ['-events', '-logfile']:
      value = options.pop(0)
      if data == '-events' :     events       = value.split(',')
      if data == '-logfile':     args.logfile = value

    elif data == '-help':
      logger.halt_with_doc('', __doc__.format(program=args.program,
                                              logfile=args.logfile))

    else:
      if data:
        args.watchpath = [os.path.abspath(x.rstrip()) for x in data.split(',')]

      if len(options) > 0:
        args.extensions = [ x for x in options ]
        options.clear()
      #endif
  #endwhile

  if not args.watchpath:
    logger.halt('ERROR: set directory to monitoring')

  if len(args.watchpath) > 0:
    for path in args.watchpath:
      if not os.path.exists(path):
        logger.warning(f'ERROR: {path} not found')

  for event in events:
    if event not in args.events:
      logger.halt(f'ERROR: {event} not recognized')
  #endfor

  if len(events) > 0:
    args.events = events

  logger.setlogfile(args.logfile)
#parse_arguments


if __name__ == "__main__":
  try:    reload(sys); sys.setdefaultencoding("utf8")
  except: pass

  if os.getuid() != 0:
    halt('ERROR: You need root privileges', 1)

  main(Logger())
