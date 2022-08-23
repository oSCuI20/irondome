# -*- coding: utf-8 -*-
#
# ./fs/integrity.py
# Eduardo Banderas Alba
# 2022-08
#
import os, sys
import hashlib

from time import sleep

from utils import checksum, fp_write, explore, Logger, dbSQLite


class FSIntegrity(object):

  basepath = os.path.dirname(os.path.abspath(sys.argv[0]))

  def __init__(self, path):
    self.database = f'{self.basepath}/.fs-integrity.sqlite3'
    self.path     = path

    self.logger = Logger()
    self.logger.debug(f'database file -> {self.database}')

    self.conn = dbSQLite(self.database)

    self.run(self.path)
    # self.__initilize_database__()
    # self.__initialize__()
  #__init__

  def run(self, path):
    i = 0
    for file in explore(path):
      f = open(file, 'rb')
      hash = hashlib.sha256(f.read()).hexdigest()
      f.close()

      self.logger.debug(f' {file}')
    #endfoe
    self.logger.debug(f'end {path}')
  #run

  def __initialize__(self):
    sql = "SELECT COUNT(*) as counter FROM sys_integrity"
    self.conn.fetchone(sql)

    self.logger.debug(f'initialize, {self.conn.result} `{sql}`')
    if self.conn.result['counter'] == 0:
      self.run(self.path)
  #__initialize__

  def __initilize_database__(self):
    sql = "SELECT name FROM sqlite_master GROUP BY 1 HAVING type='table' AND name='sys_integrity';"
    self.conn.fetchone(sql)

    if not self.conn.result:    # create table sys_integrity
      self.logger.debug(f'initialize database, {self.database}')
      sql = """
CREATE TABLE `sys_integrity` (
  `id`                INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  `path`              BLOB,
  `hash`              VARCHAR(255) NOT NULL,
  `date`              DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated`           DATETIME DEFAULT CURRENT_TIMESTAMP
);
    """
      self.conn.insert(sql)
    #endif
  #__initilize__
#class FSIntegrity


class FSIntegrityError(OSError, Exception):
  def __str__(self):
    return f'FSIntegrityError - [Errno {self.errno}] {self.strerror}'
