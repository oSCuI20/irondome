# -*- coding: utf-8 -*-
#
# ./utils/logger.py
# Eduardo Banderas Alba
# 2022-08
#
# logger
#
import sys, os

from time import strftime, localtime


class Logger:

  __fd = None

  def __init__(self, logfile=None):
    self.__verbose = bool(os.environ.get('VERBOSE', False))
    self.__debug   = bool(os.environ.get('DEBUG', False))

    self.color = None
    self.endc  = Colors.ENDC

    self.setlogfile(logfile)

  def __logging(self, msg):
    msg = msg.rstrip()
    tm  = strftime("%Y-%m-%d %H:%M:%S ", localtime())
    if   self.__verbose:
      sys.stdout.write(f'{tm} --> {self.color}{msg}{self.endc}\n')
    elif self.__debug:
      sys.stdout.write(f'{tm} --> {self.color}{msg}{self.endc}\n')

    if self.__fd:
      self.__fd.write(f'{tm} --> {msg}\n')
  #__logging

  def success(self, msg):
    self.color = Colors.GREEN
    self.__logging(f'SUCCESS - {msg}')
  #success

  def warning(self, msg):
    self.color = Colors.YELLOW
    self.__logging(f'WARNING - {msg}')
  #warning

  def critical(self, msg):
    self.color = Colors.RED
    self.__logging(f'CRITICAL - {msg}')
  #critical

  def debug(self, msg):
    self.color = Colors.BOLD
    self.__logging(f'DEBUG {msg}')
  #debug

  def halt(self, msg, code=0):
    self.color = Colors.BOLD
    sys.stdout.write(f'{self.color}{msg}{self.endc}\n')
    sys.exit(code)
  #halt

  def halt_with_doc(self, msg, doc, code=0):
    self.halt(f'{msg}\n{"-" * 80}{doc}', code)
  #halt_with_doc

  def setlogfile(self, logfile):
    if logfile:
      logdirectory = os.path.dirname(logfile)
      if not os.path.exists(logdirectory):
        os.makedirs(logdirectory)

      self.__fd = open(logfile, 'a')

  @property
  def verbose(self):
    return self.__verbose

  @verbose.setter
  def verbose(self, v):
    self.__verbose = v
#class Logger


class Colors:
  RED    = '\033[31m'
  GREEN  = '\033[32m'
  YELLOW = '\033[33m'
  BLUE   = '\033[34m'

  BOLD = '\033[;1m'
  ENDC = '\033[m'
#class Colors
