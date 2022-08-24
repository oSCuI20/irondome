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

  result = None

  def __init__(self, dbfile):
    self.dbfile  = dbfile
    self.logger  = Logger()

    self.connect = sqlite3
  #__init__

  def to_dict(self, cur, row):
    out = {}
    for idx, field in enumerate(cur.description):
      out[field[0]] = row[idx]

    return out
  #to_dict

  def parse(self, sql):
    if isinstance(sql, tuple):
      return sql

    return sql, ()
  #parse

  def fetchone(self, sql):
    sql, params = self.parse(sql)

    self.cur.execute(sql, (params))
    self.result = self.cur.fetchone()
  #fetchone

  def fetchall(self, sql):
    sql, params = self.parse(sql)

    self.cur.execute(sql, (params))
    self.result = self.cur.fetchall()
  #fetchall

  def insert(self, sql):
    sql, params = self.parse(sql)

    self.cur.execute(sql, (params))
    self.connect.commit()
  #insert

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

    self._connect = v.connect(self.dbfile, check_same_thread=False)
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
