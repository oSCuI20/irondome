# -*- coding: utf-8 -*-
#
# ./dbaccess/db_sqlite3.py
# Eduardo Banderas Alba
# 2022-07
#
# Database access
#
import os
import sqlite3

from utils import Logger


class dbSQLite(object):

  self.result = None

  def __init__(self, dbfile):
    self.dbfile  = dbfile
    self.connect = sqlite3

    self.logger  = Logger()

  def to_dict(self, cur, row):
    out = {}
    for idx, field in enumerate(cur.description):
      out[field[0]] = row[idx]

    return out

  def fetchone(self, sql):

    cur.execute(sql)
    self.result = cur.fetchone()
    cur.close()

  def insert(self, sql):

  @property
  def cur(self):
    return self._cur

  @cur.setter
  def cur(self, v):
    self._cur = v

  @property
  def connect(self):
    return self._connect

  @connect.setter
  def connect(self, v):
    if not self.dbfile:
      raise dbSQLiteException("ERROR: No database file defined")

    self._connect = v.connect(self.dbfile)
    self._connect.row_factory = self.to_dict

    self.cur = self.connect.cursor()

    self.logger.debug(f'Connected using {self.dbfile}')

  @property
  def dbfile(self):
    return self._dbfile

  @dbfile.setter
  def dbfile(self, v):
    self._dbfile = v
#class dbSQLite


class dbSQLiteException(Exception):
  def __init__(self, msg):      self.msg = msg
  def __str__(self):            return repr(self.msg)
#class dbSQLiteException
