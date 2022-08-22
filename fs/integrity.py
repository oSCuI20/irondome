# -*- coding: utf-8 -*-
#
# ./fs/integrity.py
# Eduardo Banderas Alba
# 2022-08
#
import hashlib
import os

from utils import checksum, fp_write, explore


class FSIntegrity(object):

  basepath = os.path.dirname(os.path.abspath(sys.argv[0]))

  def __init__(self, path):
    self.database = f'{self.basepath}/.fs-integrity.db'
    self.path     = path

    self.logger = Logger()
    self.logger.debug(f'database file -> {self.database}')

    self.__initilize__()
  #__init__

  def __initilize__(self):
    self.logger.debug(f'initialize database, running on folder {self.path}')
  #__initilize__
