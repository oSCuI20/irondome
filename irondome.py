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
        'modify'
        'attrib'
        'create'
        'delete'
        'delete self'
        'move from'
        'move to'
    -init-integrity
    -logfile default, {logfile}
    -help
"""
import sys, os

from threading import Thread
from time      import time, sleep, strftime, localtime

from utils import Logger, explore
from fs    import FSEvent, FSWatcher, FSWatcherError, FSIntegrity, FSIntegrityError, \
                  IOStats


class args:
  program  = sys.argv[0]
  logfile  = '/var/log/irondome/irondome.logs'
  basepath = os.path.dirname(os.path.abspath(sys.argv[0]))

  init_integrity = False

  watchpath  = None
  extensions = []
  maxmemory  = 100 # MB

  events = [
    'modify',
    'attrib',
    'create',
    'delete',
    'delete self',
    'move from',
    'move to'
  ]
#class args


def main():
  parse_arguments()

  Logger.logfile = args.logfile
  
  logger = Logger()
  logger.debug(f'args {args.__dict__}')

  integrity = FSIntegrity(args.init_integrity)
  if args.init_integrity:
    [ integrity.run(path) for path in args.watchpath ]
    logger.halt('finish')

  watchers  = FSWatcher(args.extensions)
  flags     = FSEvent.get_flags(FSEvent, args.events)

  logger.log((-1, f'running integrity file system'))

  logger.debug(f'events {args.events} flags {bin(flags)}')
  notfound = []

  # init program
  for path in args.watchpath:
    try:
      logger.log((-1, f'check integrity files in {path}'))
      sleep(1)

      integrity.run(path)

      paths = [ path ] + [ x for x in explore(path, directory=True) ]

      for p in paths:
        logger.log((-1, f'running watcher, {p}'))
        watchers.add_event(path=p, flags=flags)

    except FSIntegrityError as err:
      logger.log((-3, f'{err}, {path}'))
      logger.debug(f'{err}, {path}')

    except FSWatcherError as err:
      logger.log((-3, f'{err}, {path}'))
      logger.debug(f'{path} not found')
      notfound.append(path)
  #endfor

  logger.log((-1, f'end integrity'))

  io = IOStats(interval=1)

  if len(notfound) == len(args.watchpath):
    logger.halt(f'paths not found')

  thiostats = Thread(name='IOStats', target=io.loop)
  thmonitor = Thread(name='FSWatcher', target=watchers.loop)

  while True:
    try:
      if not thiostats.is_alive():
        logger.log((-1, 'starting iostats'))
        thiostats.start()

      if not thmonitor.is_alive():
        logger.log((-1, 'stating monitor'))
        thmonitor.start()

      sleep(0.5)
    except KeyboardInterrupt:
      io.terminate       = True
      watchers.terminate = True

      thiostats.join()
      thmonitor.join()
      break
  #endwhile
#main

def parse_arguments():
  options_ = [ '-event', '-logfile', '-init-integrity', '-help' ]
  options  = sys.argv[1:]

  logger = Logger()
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

    elif data == '-init-integrity':
      args.init_integrity = True
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
        logger.log((-2, f'ERROR: {path} not found'))

  for event in events:
    if event not in args.events:
      logger.halt(f'ERROR: {event} not recognized')
  #endfor

  if len(events) > 0:
    args.events = events
#parse_arguments


if __name__ == "__main__":
  try:    reload(sys); sys.setdefaultencoding("utf8")
  except: pass

  if os.getuid() != 0:
    print('ERROR: You need root privileges')

  main()
