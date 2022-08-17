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

from lib.inotify import *


class FSWatcher(object):
  def __init__(self):
    self.__fd = inotify_init()
    self.__lock = threading.Lock()
    self.__to_watcher = {}
  #__init__

  def __del__(self):
    if self.__fd is not None:
      self._del_watchers()
      os.close(self.__fd)
      self.__fd = None
  #__del__

  def add_event(self, path, flags=IN_ALL_EVENTS, iflags=0):
    iflags |= flags | IN_DELETE_SELF
    path = path if isinstance(path, bytes) else path.encode()
    wd = inotify_add_watch(self.__fd, path, iflags)

    if wd == -1:
      errno = get_errno()
      raise FSWatcherError(errno, strerror(errno))

    with self.__lock:
      self.__to_watcher[wd] = {
        'wd': wd,
        'path': path,
        'flags': flags
      }
  #add_event

  def read_events(self):
    """
      return IEvent object
    """
    try:
      data = os.read(self.__fd, 1024)
      for wd, mask, cookie, name in IEvent.parse(data):
        with self.__lock:
          event  = self.__to_watcher.get(wd)

        if event is not None:
          bit = 1
          while bit < 0x10000:
            if bit & mask and bit & event['flags']:
              if isinstance(name, bytes):
                name = name.decode()

              yield IEvent(event, bit, name)

            bit <<= 1
          #endwhile
        #endif
      #endfor

    except OSError as e:
      raise FSWatcherError(*e.args)
  #read_event

  def _del_watchers(self):
    with self.__lock:
      for wd in self.__to_watcher.keys():
        inotify_rm_watch(self.__fd, wd)
  #rm_watcher
#class FSWatcher



class IEvent(object):
  __Access      = IN_ACCESS
  __Modify      = IN_MODIFY
  __Attrib      = IN_ATTRIB
  __Create      = IN_CREATE
  __Delete      = IN_DELETE
  __DeleteSelf  = IN_DELETE_SELF
  __MoveFrom    = IN_MOVED_FROM
  __MoveTo      = IN_MOVED_TO
  __Open        = IN_OPEN
  __All         = IN_ALL_EVENTS

  __action_names = {
      __Access     : 'access',
      __Modify     : 'modify',
      __Attrib     : 'attrib',
      __Create     : 'create',
      __Delete     : 'delete',
      __DeleteSelf : 'delete self',
      __MoveFrom   : 'move from',
      __MoveTo     : 'move to',
      __Open       : 'open',
  }

  def __init__(self, event, action, name=''):
    self.event  = event
    self.action = action
    self.name   = name

  def __dict__(self):
    out = {}
    for k in ['event', 'action', 'name']:
      out[k] = self.__getAttirbute__(k)

    return repr(out)

  def parse(b):
    offset, by = (0, 16)

    print(b)
    while offset + by < len(b):
      wd, mask, cookie, length = unpack_from('iIII', b, offset)
      name = b[offset + by: offset + by + length].rstrip(b'\0')

      offset += by + length
      yield wd, mask, cookie, name
  #parse

  @property
  def action_name(self):
    print(self.action)
    return self.__action_names.get(self.action)

  @property
  def path(self):
    return self.event['path']

  @property
  def Access(self):
    return self.__Access

  @property
  def Modify(self):
    return self.__Modify

  @property
  def Attrib(self):
    return self.__Attrib

  @property
  def Create(self):
    return self.__Create

  @property
  def Delete(self):
    return self.__Delete

  @property
  def DeleteSelf(self):
    return self.__DeleteSelf

  @property
  def MoveFrom(self):
    return self.__MoveFrom

  @property
  def MoveTo(self):
    return self.__MoveTo

  @property
  def All(self):
    return self.__All
#class IEvents


class FSWatcherError(OSError, Exception):
  pass
