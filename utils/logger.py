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

  fd = None
  logfile = None

  def __init__(self):
    self.__verbose = bool(os.environ.get('VERBOSE', False))
    self.__debug   = bool(os.environ.get('DEBUG', False))

    self.color = None
    self.endc  = Colors.ENDC
    self.setlogfile()

  def __logging(self, msg):
    msg = msg.rstrip()
    tm  = strftime("%Y-%m-%d %H:%M:%S ", localtime())

    if self.__debug and not self.__verbose or self.__verbose:
      sys.stdout.write(f'{tm} --> {self.color}{msg}{self.endc}\n')

    if self.fd:
      self.fd.write(f'{tm} --> {msg}\n')
      self.fd.flush()
      self.fd.seek(0)

  #__logging

  def log(self, _msg):
    def success(msg):
      self.color = Colors.GREEN
      self.__logging(f'Ok - {msg}')
    #success

    def warning(msg):
      self.color = Colors.YELLOW
      self.__logging(f'WARNING - {msg}')
    #warning

    def error(msg):
      self.color = Colors.RED
      self.__logging(f'CRITICAL - {msg}')
    #error

    log = { -1: success, -2: warning, -3: error }

    log[_msg[0]](_msg[1])
  #log

  def debug(self, msg):
    self.color = Colors.BOLD
    if self.__debug:
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

  def setlogfile(self):
    if self.logfile:
      logdirectory = os.path.dirname(self.logfile)
      if not os.path.exists(logdirectory):
        os.makedirs(logdirectory)

      self.fd = open(self.logfile, 'a+')
    #endif
  #setlogfile

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
