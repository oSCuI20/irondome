# -*- coding: utf-8 -*-
#
# ./fs/monitor.py
# Eduardo Banderas Alba
# 2022-08
#
# Object to monitoring filesystem
#
import os

from threading import Lock
from time      import time
from ctypes    import c_int, get_errno
from fcntl     import ioctl
from termios   import FIONREAD
from io        import FileIO

from fs    import *
from utils import ToObject, Logger


class FSWatcher(FileIO):

  def __init__(self, extensions=[]):
    FileIO.__init__(self, inotify_init(os.O_NONBLOCK))

    self.__lock = Lock()
    self.__to_watcher = {}
    self.__extensions = extensions

    self.__integrity = FSIntegrity()

    if not isinstance(self.__extensions, list):
      raise FSWatcherError(-2, 'type of extensions not valid')

    self.terminate = False
    self.logger = Logger()
    self.logger.debug(f'__to_watcher -> {self.__to_watcher}')
  #__init__

  def __del__(self):
    self._del_watchers()
  #__del__

  def loop(self):
    while True:
      if self.terminate:
        break

      for event in self.read_events():
        self.logger.log(event)

      sleep(0.2)
    #endwhile
  #loop

  def add_event(self, path, flags=IN_ALL_EVENTS, wd_parent=0, iflags=0):
    iflags |= flags | IN_ALL_EVENTS | IN_ONLYDIR
    path = path if isinstance(path, bytes) else path.encode()
    wd = inotify_add_watch(self.fileno(), path, iflags)

    self.logger.log((-1, f'new watcher -> wd {wd}, path {path} with parent {wd_parent}'))

    if wd == -1:
      errno = get_errno()
      raise FSWatcherError(errno, strerror(errno))

    with self.__lock:
      self.__to_watcher[wd] = ToObject(**{
        'wd': wd,
        'path': path,
        'wd_parent': wd_parent,
        'flags': flags
      })
  #add_event

  def __handler(self, entry, mask, event, wd):
    self.result = None
    if mask & IN_ISDIR:  # remove or add new watchers
      exists = self._watcher_exists(entry)

      if os.path.isdir(entry) and not exists:
        self.add_event(entry, event.flags, wd)

      if exists and mask & IN_DELETE:
        with self.__lock:
          self._del_watcher_by_path(entry)
    #endif

    flag = mask & event.flags
    if flag:
      fsevent = FSEvent(event, flag, entry)
      self.result = (-1, f'{fsevent.events_name} to `{entry}`')

    if mask & IN_MODIFY or mask & IN_MOVED_TO or mask & IN_MOVED_FROM:
      if not self.__integrity.validate(entry.encode()):
        info = self.__integrity.get(entry.encode())
        hash = self.__integrity.get_hash(entry.encode())

        self.result = (-2, f'{fsevent.events_name} `{entry}`')

        if info and info['hash'] != hash:
          self.result = (-3, f'{fsevent.events_name} `{entry}` has been modified')
    #endif
  #__handler

  def read_events(self, timeout=1):
    try:
      entry, data, avail = (None, b'', c_int())
      ioctl(self, FIONREAD, avail)
      if not avail.value:
        return

      data = os.read(self.fileno(), avail.value)
      for wd, mask, cookie, name in FSEvent.parse(data):
        with self.__lock:
          event = self.__to_watcher.get(wd)

        if   not event or \
             mask & IN_DONT_FOLLOW or \
             mask & IN_EXCL_UNLINK:
          continue #exclude sym links

        #TODO extensions filter
        entry  = f'{os.path.join(event.path, name).decode().rstrip("/")}'
        self.logger.debug(f'read_events: wd {wd}, cookie {cookie}, entry {entry}, mask {hex(mask)}')

        self.__handler(entry, mask, event, wd)

        if mask & IN_ISDIR:
          continue

        if mask & IN_IGNORED:
          with self.__lock:
            try:               del self.__to_watcher[wd]
            except KeyError:   pass
        #endif

        if self.result:
          yield self.result
        #endif
      #endfor

    except OSError as e:
      raise FSWatcherError(*e.args)
  #read_event

  def _check_extension_file(self, filepath):
    pass
  #_exclude_file

  def _watcher_exists(self, path):
    path = path if isinstance(path, bytes) else path.encode()

    for wd in self.__to_watcher.keys():
      watcher = self.__to_watcher.get(wd)
      if watcher.path == path:
        return True
    #endfor

    return False
  #_watcher_exists

  def _del_watcher_by_path(self, path):
    path = path if isinstance(path, bytes) else path.encode()
    wds = list(self.__to_watcher.keys())
    for wd in wds:
      watcher = self.__to_watcher.get(wd)
      if watcher.path == path:
        del self.__to_watcher[wd]
        inotify_rm_watch(self.fileno(), wd)
  #_del_watcher_by_path

  def _del_watchers(self):
    with self.__lock:
      for wd in self.__to_watcher.keys():
        inotify_rm_watch(self.fileno(), wd)
  #rm_watcher
#class FSWatcher


class FSWatcherError(OSError, Exception):

  def __str__(self):
    return f'FSWatcherError - [Errno {self.errno}] {self.strerror}'
