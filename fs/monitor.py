# -*- coding: utf-8 -*-
#
# ./fs/monitor.py
# Eduardo Banderas Alba
# 2022-08
#
# Object to monitoring filesystem
#
import os
import threading
import traceback

from time    import time
from ctypes  import c_int, get_errno
from fcntl   import ioctl
from termios import FIONREAD
from io      import FileIO

from fs    import *
from utils import ToObject, Logger


class FSWatcher(FileIO):

  def __init__(self, extensions=[]):
    FileIO.__init__(self, inotify_init(os.O_NONBLOCK))
    #self.__fd   = inotify_init(os.O_NONBLOCK)
    self.__lock = threading.Lock()
    self.__to_watcher = {}
    self.__extensions = extensions

    self.__events_entry = []
    self.__last_entry   = None
    self.__timeout      = time()

    if not isinstance(self.__extensions, list):
      raise FSWatcherError(-2, 'type of extensions not valid')

    self.logger = Logger()
    self.logger.debug(f'__to_watcher -> {self.__to_watcher}')
  #__init__

  # def __del__(self):
  #   if self.__fd is not None:
  #     self._del_watchers()
  #     os.close(self.__fd)
  #     self.__fd = None
  # #__del__

  def add_event(self, path, flags=IN_ALL_EVENTS, wd_parent=0, iflags=0):
    iflags |= flags | IN_ALL_EVENTS
    path = path if isinstance(path, bytes) else path.encode()
    wd = inotify_add_watch(self.fileno(), path, iflags)

    self.logger.debug(f'new watcher -> wd {wd}, path {path} with parent {wd_parent}')

    if wd == -1:
      errno = get_errno()
      raise FSWatcherError(errno, strerror(errno))

    self.logger.debug(f'add_event __lock {self.__lock}')
    with self.__lock:
      self.logger.debug(f'add_event with __lock {self.__lock}')
      self.__to_watcher[wd] = ToObject(**{
        'wd': wd,
        'path': path,
        'wd_parent': wd_parent,
        'flags': flags
      })
  #add_event

  def __handler(self, mask, path, flags, wd):
    if mask & IN_ISDIR:  # remove or add new watchers
      exists = self._watcher_exists(path)

      if os.path.isdir(path) and not exists:
        self.add_event(path, flags, wd)

      if exists and mask & IN_DELETE:
        with self.__lock:
          self._del_watcher_by_path(path)
    #endif

    if mask & IN_MODIFY:
      #TODO manage integrity
      pass
    #endif
  #__handler

  def read_events(self, timeout=1):
    try:
      entry, data, avail = (None, b'', c_int())
      ioctl(self, FIONREAD, avail)
      if not avail.value:
        if (time() - self.__timeout) > timeout:
          if len(self.__events_entry) > 0:
            yield self.__result()
        #endif

        return
      #endif

      self.__timeout = time()
      data = os.read(self.fileno(), avail.value)

      for wd, mask, cookie, name in FSEvent.parse(data):
        self.logger.debug(f'read_events __lock {self.__lock}')
        with self.__lock:
          self.logger.debug(f'read_events with __lock {self.__lock}')
          event = self.__to_watcher.get(wd)

        if   not event or \
             mask & IN_DONT_FOLLOW or \
             mask & IN_EXCL_UNLINK:
          continue #exclude sym links

        #TODO extensions filter
        entry  = f'{os.path.join(event.path, name).decode().rstrip("/")}'
        self.logger.debug(f'read_events, mask {bin(mask)}')
        self.logger.debug(f'read_events, entry {entry}')

        self.__handler(mask, entry, event.flags, wd)
        if mask & IN_ISDIR and event.wd_parent:
          continue

        flag = mask & event.flags
        if flag:
          fsevent = FSEvent(event, flag, entry)
          if  entry != self.__last_entry and \
              self.__last_entry and len(self.__events_entry) > 0:
            yield self.__result()

          self.__last_entry = entry
          if fsevent.events_name not in self.__events_entry:
            self.__events_entry.append(fsevent.events_name)
        #endif
      #endfor

    except OSError as e:
      raise FSWatcherError(*e.args)
  #read_event

  def __result(self):
    self.logger.debug(f'__last_entry {self.__last_entry}')
    self.logger.debug(f'__events_entry {self.__events_entry}')

    with self.__lock:
      e = list(self.__events_entry)
      self.__events_entry.clear()

    return f'`{self.__last_entry}`: -> {" ".join(e)}'
  #__result

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
  #_del_watcher_by_path

  def _del_watchers(self):
    with self.__lock:
      for wd in self.__to_watcher.keys():
        inotify_rm_watch(self.__fd, wd)
  #rm_watcher
#class FSWatcher


class FSWatcherError(OSError, Exception):

  def __str__(self):
    return f'FSWatcherError - [Errno {self.errno}] {self.strerror}'
