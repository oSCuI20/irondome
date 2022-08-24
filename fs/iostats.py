# -*- coding: utf-8 -*-
#
# ./fs/iostats.py
# Eduardo Banderas Alba
# 2022-08
#
# Get read/write in bytes per seconds
#
import os

from time  import sleep
from utils import Logger

class IOStats(object):

  mapping = {
    'reads_completed': 0,
    'reads_merged': 1,
    'sectors_read': 2,
    'millsec_spent_reading': 3,
    'writes_completed': 4,
    'writes_merged': 5,
    'sectors_written': 6,
    'millsec_spent_writing': 7,
    'io_currently_progress': 8,
    'io_millsec_spent_doing': 9
  }

  stats_mapping = {
    'sectors_read': 'rb/s',
    'sectors_written': 'wb/s'
  }

  def __init__(self, interval=0,
                     abuse_warning=150*1024,
                     abuse_critical=10*1024*1024):
    self.disks = {}
    self.stats = {
      'reads_completed': 0,
      'reads_merged': 0,
      'sectors_read': 0,
      'millsec_spent_reading': 0,
      'writes_completed': 0,
      'writes_merged': 0,
      'sectors_written': 0,
      'millsec_spent_writing': 0,
      'io_currently_progress': 0,
      'io_millsec_spent_doing': 0
    }

    self.interval    = interval
    self.sector_size = 512

    self.read_disks_abuse = {}
    self.read_disks_abuse_max_counter = 10
    self.read_disks_abuse_warning  = abuse_warning   # default, 10 MB
    self.read_disks_abuse_critical = abuse_critical  # default, 10 MB

    self.terminate = False
    self.logger = Logger()

    self.__initialize__()
  #__init__

  def __initialize__(self):
    #define S_VALUE(m,n,p)		(((double) ((n) - (m))) / (p) * 100)

    path = '/sys/block'
    for disk in os.listdir(path):
      if disk.startswith('loop'):
        continue

      self.disks.update({
        disk: {
          'path' : f'{path}/{disk}',
          'fd'   : open(f'{path}/{disk}/stat', 'r'),
          'stats': self.stats.copy(),
          'rb/s': 0,
          'wb/s': 0,
          'partitions': {}
        }
      })

      self.read_disks_abuse.update({
        disk: []
      })

      partition_path = self.disks[disk]['path']
      for partition in os.listdir(partition_path):
        if not partition.startswith(disk):
          continue

        self.disks[disk]['partitions'].update({
          partition: {
            'fd': open(f'{partition_path}/{partition}/stat', 'r'),
            'stats': self.stats.copy(),
            'rb/s': 0,
            'wb/s': 0
          }
        })
    #endfor
  #__initialize__

  def loop(self, flags=0):
    #flags => unit for show data (not implement)
    while True:
      if self.terminate:
        break

      self.diskstats()
      for disk in self.disks.keys():
        self.read_disks_abuse[disk].append(self.disks[disk]['rb/s'])

        if len(self.read_disks_abuse[disk]) >= self.read_disks_abuse_max_counter:
          abuse = sum(self.read_disks_abuse[disk]) / self.read_disks_abuse_max_counter

          if abuse > self.read_disks_abuse_warning:
            self.logger.log((-3, f'reading abuse in {disk}, {abuse / 1024} kB/s'))

          elif abuse > self.read_disks_abuse_warning:
            self.logger.log((-2, f'reading abuse in {disk}, {abuse / 1024} kB/s'))

          self.read_disks_abuse[disk].pop(0)
        #endif
      #endfor

      sleep(self.interval)
    #endwhile
  #loop

  def diskstats(self):
    for disk in self.disks.keys():
      fd = self.disks[disk]['fd']
      previous = self.disks[disk]['stats'].copy()
      current  = self.__read__(fd)
      bps      = self.get_stats((previous, current))

      self.disks[disk]['stats'] = current
      self.disks[disk]['rb/s']  = bps['rb/s']
      self.disks[disk]['wb/s']  = bps['wb/s']

      for partition in self.disks[disk]['partitions'].keys():
        fd = self.disks[disk]['partitions'][partition]['fd']
        previous = self.disks[disk]['partitions'][partition]['stats'].copy()
        current  = self.__read__(fd)
        bps      = self.get_stats((previous, current))

        self.disks[disk]['partitions'][partition]['stats'] = current
        self.disks[disk]['partitions'][partition]['rb/s']  = bps['rb/s']
        self.disks[disk]['partitions'][partition]['wb/s']  = bps['wb/s']
      #endfor
    #endfor
  #diskstats

  def get_stats(self, v, stats=['sectors_read', 'sectors_written']):
    #v => tuple(Dict(previous), Dict(current))
    previous, current = v

    out = {}
    for stat in stats:
      if previous[stat] == 0:
        previous[stat] = current[stat]

      key = self.stats_mapping[stat]

      out[key] = self.__value__((previous[stat], current[stat]))
    #endfor

    return out
  #get_stats

  def __read__(self, fd):
    fd.seek(0)
    read_stats = fd.read(1024).strip().split()
    stats = self.stats.copy()
    for key, pos in self.mapping.items():
      stats[key] = float(read_stats[pos])

    return stats
  #__read__

  def __value__(self, v):
    #v => tuple(previous, current)
    iop, ioc = v
    # return bytes
    return ((ioc * self.sector_size) - (iop * self.sector_size)) / self.interval
  #__value__
#class IOStats
