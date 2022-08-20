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

from ctypes import get_errno

from fs.inotify import *
from utils.utils import ToObject


class FSWatcher(object):

  def __init__(self, extensions=[]):
    self.__fd   = inotify_init()
    self.__lock = threading.Lock()
    self.__to_watcher  = {}
    self.__extensions  = extensions

    if not isinstance(self.__extensions, list):
      raise FSWatcherError(-2, 'type of extensions not valid')
  #__init__

  def __del__(self):
    if self.__fd is not None:
      self._del_watchers()
      os.close(self.__fd)
      self.__fd = None
  #__del__

  def add_event(self, path, flags=IN_ALL_EVENTS, iflags=0):
    iflags |= flags | IN_ALL_EVENTS
    path = path if isinstance(path, bytes) else path.encode()
    wd = inotify_add_watch(self.__fd, path, iflags)

    if wd == -1:
      errno = get_errno()
      print(FSWatcherError(errno, strerror(errno)))
      return

    with self.__lock:
      self.__to_watcher[wd] = ToObject(**{
        'wd': wd,
        'path': path,
        'flags': flags
      })
  #add_event

  def read_events(self):
    try:
      events, filepath = ([], None)
      data = os.read(self.__fd, 1024)
      for wd, mask, cookie, name in IEvent.parse(data):
        with self.__lock:
          event = self.__to_watcher.get(wd)

        if not event:
          continue

        #TODO exclude or extensions to watcher
        filepath = f'{event.path.decode()}'
        if isinstance(name, bytes):
          name = name.decode()

        filepath += f'/{name}' if name else ''

        bit = 1
        while bit < 0x10000:
          if mask & IN_DONT_FOLLOW || mask & IN_EXCL_UNLINK:
            continue #exclude sym links

          if mask & IN_ISDIR:
            # remove or add new watchers
            exists = self._watcher_exists(filepath)
            if os.path.isdir(filepath) and not exists:
              self.add_event(filepath, event.flags)

            if exists and (mask & IN_DELETE) == IN_DELETE:
              self._del_watcher_by_path(filepath)
          #endif

          if (mask & IN_MODIFY) == IN_MODIFY:
            #TODO update hash
            #TODO check entropy
            pass
          #endif

          if bit & mask and bit & event.flags:
            yield f'`{filepath}`: -> {IEvent(event, bit, filepath).action_name}'
          #endif

          bit <<= 1
        #endwhile
      #endfor

    except OSError as e:
      raise FSWatcherError(*e.args)
  #read_event

  def _checksum(self, filepath):
    pass
  #checksump

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
