# -*- coding: utf-8 -*-
#
# ./fs/inotify.py
# Eduardo Banderas Alba
# 2022-08
#
# Binding inotify function from libc
#
from ctypes import CDLL, CFUNCTYPE, \
                   c_char_p, c_int, c_uint32
from struct import unpack_from

libc = CDLL('libc.so.6')

strerror = CFUNCTYPE(c_char_p, c_int)(
  ('strerror', libc),
)

inotify_init = CFUNCTYPE(c_int, use_errno=True)(
  ('inotify_init1', libc),
)

inotify_add_watch = CFUNCTYPE(c_int, c_int, c_char_p, c_uint32, use_errno=True)(
  ('inotify_add_watch', libc),
)

inotify_rm_watch = CFUNCTYPE(c_int, c_int, c_int, use_errno=True)(
  ('inotify_rm_watch', libc),
)

# Define constants
## Ref. https://github.com/torvalds/linux/blob/master/include/uapi/linux/inotify.h
## the following are legal, implemented events that user-space can watch for
IN_ACCESS        = 0x00000001	   # File was accessed
IN_MODIFY        = 0x00000002	   # File was modified
IN_ATTRIB        = 0x00000004	   # Metadata changed
IN_CLOSE_WRITE   = 0x00000008	   # Writtable file was closed
IN_CLOSE_NOWRITE = 0x00000010	   # Unwrittable file closed
IN_OPEN          = 0x00000020	   # File was opened
IN_MOVED_FROM    = 0x00000040	   # File was moved from X
IN_MOVED_TO      = 0x00000080	   # File was moved to Y
IN_CREATE        = 0x00000100	   # Subfile was created
IN_DELETE        = 0x00000200	   # Subfile was deleted
IN_DELETE_SELF   = 0x00000400	   # Self was deleted
IN_MOVE_SELF     = 0x00000800	   # Self was moved

## the following are legal events.  they are sent as needed to any watch
IN_UNMOUNT    =	0x00002000	     # Backing fs was unmounted
IN_Q_OVERFLOW = 0x00004000	     # Event queued overflowed
IN_IGNORED    = 0x00008000	     # File was ignored

## = helper events
IN_CLOSE = (IN_CLOSE_WRITE | IN_CLOSE_NOWRITE) # close
IN_MOVE  = (IN_MOVED_FROM | IN_MOVED_TO)       # moves

## special flags
IN_ONLYDIR     = 0x01000000	     # only watch the path if it is a directory
IN_DONT_FOLLOW = 0x02000000	     # don't follow a sym link
IN_EXCL_UNLINK = 0x04000000	     # exclude events on unlinked objects
IN_MASK_CREATE = 0x10000000	     # only create watches
IN_MASK_ADD    = 0x20000000	     # add to the mask of an already existing watch
IN_ISDIR       = 0x40000000	     # event occurred against dir
IN_ONESHOT     = 0x80000000	     # only send event once

IN_ALL_EVENTS = (IN_ACCESS | IN_MODIFY | IN_ATTRIB | IN_CLOSE_WRITE | \
                 IN_CLOSE_NOWRITE | IN_OPEN | IN_MOVED_FROM | \
                 IN_MOVED_TO | IN_DELETE | IN_CREATE | IN_DELETE_SELF | IN_MOVE_SELF)


class FSEvent(object):
  __Access      = IN_ACCESS
  __Modify      = IN_MODIFY
  __Attrib      = IN_ATTRIB
  __Create      = IN_CREATE
  __Delete      = IN_DELETE
  __DeleteSelf  = IN_DELETE_SELF
  __MoveFrom    = IN_MOVED_FROM
  __MoveTo      = IN_MOVED_TO
  __Open        = IN_OPEN
  __Close_WR    = IN_CLOSE_WRITE
  __Close_NOWR  = IN_CLOSE_NOWRITE
  __All         = IN_ALL_EVENTS

  __events_name = {
      __Access     : 'access',
      __Modify     : 'modify',
      __Attrib     : 'attrib',
      __Create     : 'create',
      __Delete     : 'delete',
      __DeleteSelf : 'delete self',
      __MoveFrom   : 'move from',
      __MoveTo     : 'move to',
      __Open       : 'open',
      __Close_WR   : 'closed',
      __Close_NOWR : 'closed',
  }

  def __init__(self, event, action, name=''):
    self.event  = event
    self.action = action
    self.name   = name
  #__init__

  def __dict__(self):
    out = {}
    for k in ['event', 'action', 'name']:
      out[k] = self.__getAttirbute__(k)

    return repr(out)
  #__dict__

  def parse(b):
    offset, by = (0, 16)

    while offset + by < len(b):
      wd, mask, cookie, length = unpack_from('iIII', b, offset)
      name = b[offset + by: offset + by + length].rstrip(b'\0')

      offset += by + length
      yield wd, mask, cookie, name
  #parse

  def get_flags(self, action_names):
    flags = self.__All

    if isinstance(action_names, list) and len(action_names) > 0:
      flags = 0
      for flag, map in self.__events_name.items():
        if map in action_names:
          flags |= flag
    #enmdif

    return flags
  #get_flags

  @property
  def events_name(self):
    return self.__events_name.get(self.action)

  @property
  def path(self):
    return self.event.path

  @property
  def flags(self):
    return self.event.flags

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
#class FSEvent
