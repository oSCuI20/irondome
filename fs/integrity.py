# -*- coding: utf-8 -*-
#
# ./fs/integrity.py
# Eduardo Banderas Alba
# 2022-08
#
import os, sys
import hashlib

from utils import checksum, fp_write, explore, Logger, dbSQLite


class FSIntegrity(object):

  basepath = os.path.dirname(os.path.abspath(sys.argv[0]))

  def __init__(self, path):
    self.database = f'{self.basepath}/.fs-integrity.sqlite3'
    self.path     = path

    self.logger = Logger()
    self.logger.debug(f'database file -> {self.database}')

    self.__sqlite =

    self.conn = dbSQLite(self.database)

    self.__initilize__()
  #__init__

  def __initilize__(self):
    self.logger.debug(f'initialize database, {self.database}')

    sql = "SELECT name FROM sqlite_master GROUP BY 1 HAVING type='table' AND name='syscheck';"

    cur = self.conn.cursor()
    cur.execute(sql)
    self.__conn.commit()

    sql = """
CREATE TABLE `syscheck` (
  `id`                INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  `path`              BLOB,
  `hash`              VARCHAR(255) NOT NULL,
  `date`              DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated`           DATETIME DEFAULT CURRENT_TIMESTAMP
);
    """


    cur.close()
  #__initilize__

  def conn():
      doc = "The conn property."
      def fget(self):
          return self._conn
      def fset(self, value):
          self._conn = value
      def fdel(self):
          del self._conn
      return locals()
  conn = property(**conn())
#class FSIntegrity
