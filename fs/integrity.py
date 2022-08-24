# -*- coding: utf-8 -*-
#
# ./fs/integrity.py
# Eduardo Banderas Alba
# 2022-08
#
import os, sys
import hashlib

from time import time, sleep

from utils import *


class FSIntegrity(object):

  basepath = os.path.dirname(os.path.abspath(sys.argv[0]))
  buffer   = 65535

  def __init__(self, initializedb=False, updatedb=True):
    self.database = f'{self.basepath}/.fs-integrity.sqlite3'
    self.logger   = Logger()

    self.__initialize__()

    if initializedb:
      self.__initilize_database__()

    if not self.__check_if_table_exists__():
      raise FSIntegrityError(-1, 'ERROR: Integrity database not initialize')

    if not initializedb:
      count = self.count()
      if not count:
        raise FSIntegrityError(-1, 'ERROR: Integrity database not initialize')
    #endif
  #__init__

  def run(self, path):
    paths = [ x for x in explore(path) ]
    while True:
      if len(paths) == 0:
        break #endwhile

      filepath = paths.pop()
      if not os.path.isfile(filepath):
        self.logger.debug(f'ignore file {filepath}')
        continue

      hash = self.get_hash(filepath)

      self.__add__(filepath.encode(), hash)
      self.logger.debug(f'{filepath} {hash}')
    #endwhile
  #run

  def get_hash(self, filepath):
    if not os.path.isfile(filepath):
      return

    hash = hashlib.sha256()
    with open(filepath, 'rb') as fr:
      while True:
        data = fr.read(self.buffer)
        if not data:
          break

        hash.update(data)
      #endwhile
      fr.flush()

    return hash.hexdigest()
  #get_hash

  def validate(self, fullpath):
    self.get(fullpath)

    return self.conn.result and self.conn.result['hash'] == self.get_hash(fullpath)
  #validate

  def remove(self, fullpath):
    self.get(fullpath)
  #remove

  def get(self, fullpath):
    sql = 'SELECT * FROM sys_integrity WHERE uid = ? LIMIT 1'

    self.conn.fetchone((sql, (hashlib.sha256(fullpath).hexdigest(),)))

    return self.conn.result
  #get

  def count(self):
    sql = "SELECT COUNT(*) as counter FROM sys_integrity"
    self.conn.fetchone(sql)

    return self.conn.result if not self.conn.result else self.conn.result['counter']
  #count

  def __add__(self, fullpath, hash):
    tm = int(time())
    self.get(fullpath)

    if self.conn.result and self.conn.result['id']:  # Update
      if self.conn.result['hash'] == hash:
        return

      sql  = 'UPDATE sys_integrity SET hash = ?, date = ? WHERE id = ?'
      vals = (hash, tm, self.conn.result['id'])

    else:
      sql  = 'INSERT INTO sys_integrity (`uid`, `path`, `hash`, `date`) ' + \
             'VALUES (?, ?, ?, ?)'
      vals = (hashlib.sha256(fullpath).hexdigest(), fullpath, hash, tm)

    self.conn.insert((sql, vals))
  #__add__

  def __initialize__(self):
    self.logger.debug(f'initialize, database file -> {self.database}')
    self.conn = dbSQLite(self.database)
  #__initialize__

  def __initilize_database__(self):
    self.logger.debug(f'initialize database, {self.database}')

    if self.__check_if_table_exists__():
      question = input('sys_integrity table exists, do you want to continue? [y/n]')
      if question.lower() == 'y':
        sql = "DROP TABLE sys_integrity"
        self.conn.insert(sql)
      else:
        self.logger.halt('Cancel')
    #endif

    sql = """
CREATE TABLE `sys_integrity` (
`id`                INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
`uid`               VARCHAR(255) NOT NULL,
`path`              BLOB,
`hash`              VARCHAR(255) NOT NULL,
`date`              DATETIME DEFAULT CURRENT_TIMESTAMP,
`updated`           DATETIME DEFAULT CURRENT_TIMESTAMP
);
  """
    self.conn.insert(sql)
  #__initilize__

  def __check_if_table_exists__(self):
    sql = "SELECT name FROM sqlite_master GROUP BY 1 HAVING type='table' AND name='sys_integrity';"
    self.conn.fetchone(sql)

    return self.conn.result
#class FSIntegrity


class FSIntegrityError(OSError, Exception):
  def __str__(self):
    return f'FSIntegrityError - [Errno {self.errno}] {self.strerror}'
