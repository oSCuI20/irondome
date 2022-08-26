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

  ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK']) #Clock ticks per seconds

  # /proc/stat position of value
  # ignore position 0 its the name of cpu
  __CPU_USER    = 1
  __CPU_NICE    = 2
  __CPU_SYSTEM  = 3
  __CPU_IDLE    = 4
  __CPU_IOWAIT  = 5
  __CPU_IRQ     = 6
  __CPU_SOFTIRQ = 7
  __CPU_STEAL   = 8
  __CPU_GUEST   = 9

  # /sys/block/<disk>/stat and /sys/block/<disk>/<partition>/stat position of value
  __READ_COMPLETED         = 0
  __READ_MERGED            = 1
  __SECTORS_READ           = 2
  __MILLSEC_SPENT_READING  = 3
  __WRITES_COMPLETED       = 4
  __WRITES_MERGED          = 5
  __SECTORS_WRITTEN        = 6
  __MILLSEC_SPENT_WRITTING = 7
  __IO_CURRENTLY_PROGRESS  = 8
  __IO_MILLSEC_SPENT_DOING = 9

  __cpu_mapping__ = {
    'user': __CPU_USER,
    'nice': __CPU_NICE,
    'system': __CPU_SYSTEM,
    'idle': __CPU_IDLE,
    'iowait': __CPU_IOWAIT,
    'irq': __CPU_IRQ,
    'softirq': __CPU_SOFTIRQ,
    'steal': __CPU_STEAL,
    'guest': __CPU_GUEST
  }

  __disk_mapping__ = {
    'reads_completed': __READ_COMPLETED,
    'reads_merged': __READ_MERGED,
    'sectors_read': __SECTORS_READ,
    'millsec_spent_reading': __MILLSEC_SPENT_READING,
    'writes_completed': __WRITES_COMPLETED,
    'writes_merged': __WRITES_MERGED,
    'sectors_written': __SECTORS_WRITTEN,
    'millsec_spent_writing': __MILLSEC_SPENT_WRITTING,
    'io_currently_progress': __IO_CURRENTLY_PROGRESS,
    'io_millsec_spent_doing': __IO_MILLSEC_SPENT_DOING
  }

  __disks_stats_mapping__ = {
    'sectors_read': 'rb/s',
    'sectors_written': 'wb/s'
  }

  def __init__(self, interval=0,
                     abuse_warning=150*1024,
                     abuse_critical=10*1024*1024):
    self.cpus  = {}
    self.disks = {}

    self.interval    = interval
    self.sector_size = 512

    self.read_disks_abuse = {}
    self.read_disks_abuse_max_counter = 10
    self.read_disks_abuse_warning  = abuse_warning
    self.read_disks_abuse_critical = abuse_critical

    self.terminate = False
    self.logger = Logger()

    self.__initialize__()
  #__init__

  def __initialize__(self):
    self.__initialize_cpus_stats__()
    self.__initialize_disks_stats__()
  #__initialize__

  def __initialize_cpus_stats__(self):
    cpuinfo = '/proc/cpuinfo'
    cpustat = '/proc/stat'

    self.cpus.update({
      'fd': open(cpustat, 'r'),
      'cpu': { key: 0 for key in self.__cpu_mapping__.keys() }
    })

    with open(cpuinfo, 'r') as fr:
      info = fr.read()
      for c in info.split('\n'):
        if c.startswith('processor'):
          cpuN = f'cpu{c.split(":")[1].strip()}'
          self.cpus.update({
            cpuN: { key: 0 for key in self.__cpu_mapping__.keys() },
          })
        #endif
      #endfor
    #endwith

    self.logger.debug(f'CPUS: {self.cpus}')
  #__initialize__cpus_stats__

  def __initialize_disks_stats__(self):
    path = '/sys/block'
    for disk in os.listdir(path):
      if disk.startswith('loop'):
        continue

      self.disks.update({
        disk: {
          'path' : f'{path}/{disk}',
          'fd'   : open(f'{path}/{disk}/stat', 'r'),
          'stats': { key: 0 for key in self.__disk_mapping__.keys() },
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
            'stats': { key: 0 for key in self.__disk_mapping__.keys() },
            'rb/s': 0,
            'wb/s': 0
          }
        })
    #endfor

    self.logger.debug(f'DISKS: {self.disks}')
  #__initialize_disks_stats__

  def loop(self, flags=0):
    #flags => unit for show data (not implement)
    while True:
      if self.terminate:
        break

      self.cpustats()
      cpu_usage = []
      log_level = -1
      for cpu in self.cpus.keys():
        if cpu in ['fd']:
          continue

        usage = self.cpus[cpu]['usage']

        if cpu not in ['cpu']:
          if usage > 35 and usage <= 85:
            log_level = -2
          elif usage > 85:
            log_level = -3

        cpu_usage.append(f'{usage}')
      #endfor

      self.logger.log((log_level, f'usage {cpu_usage}'))

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

  def cpustats(self):
    fd = self.cpus['fd']
    for cpu in self.cpus.keys():
      if cpu in ['fd', 'usage']:
        continue

      previous = self.cpus[cpu].copy()
      current  = self.__read_cpustats__(fd, cpu)

      current['usage'] = self.get_cpustatistics((previous, current))

      self.cpus.update({
        cpu: current
      })
    #endfor
  #cpustats

  def diskstats(self):
    for disk in self.disks.keys():
      fd = self.disks[disk]['fd']
      previous = self.disks[disk]['stats'].copy()
      current  = self.__read_diskstat__(fd)
      bps      = self.get_diskstatistics((previous, current))

      self.disks[disk]['stats'] = current
      self.disks[disk]['rb/s']  = bps['rb/s']
      self.disks[disk]['wb/s']  = bps['wb/s']

      for partition in self.disks[disk]['partitions'].keys():
        fd = self.disks[disk]['partitions'][partition]['fd']
        previous = self.disks[disk]['partitions'][partition]['stats'].copy()
        current  = self.__read_diskstat__(fd)
        bps      = self.get_diskstatistics((previous, current))

        self.disks[disk]['partitions'][partition]['stats'] = current
        self.disks[disk]['partitions'][partition]['rb/s']  = bps['rb/s']
        self.disks[disk]['partitions'][partition]['wb/s']  = bps['wb/s']
      #endfor
    #endfor
  #diskstats

  def get_cpustatistics(self, v):
    previous, current = v

    cpu_previous_sum = sum([y for x, y in previous.items() if x not in ['usage']])
    cpu_current_sum  = sum([y for x, y in current.items() if x not in ['usage']])

    cpu_delta = cpu_current_sum - cpu_previous_sum
    cpu_idle  = current['idle'] - previous['idle']
    cpu_inuse = cpu_delta - cpu_idle

    return round(100 * cpu_inuse / cpu_delta, 2)
  #get_cpustatistics

  def get_diskstatistics(self, v, stats=['sectors_read', 'sectors_written']):
    #v => tuple(Dict(previous), Dict(current))
    previous, current = v

    out = {}
    for stat in stats:
      if previous[stat] == 0:
        previous[stat] = current[stat]

      key = self.__disks_stats_mapping__[stat]

      out[key] = self.__value__((previous[stat], current[stat]))
    #endfor

    return out
  #get_diskstatistics

  def __read_cpustats__(self, fd, cpu):
    fd.seek(0)
    read_line_stats = fd.read().split('\n')
    read_stats = []
    while len(read_line_stats) > 0:
      line = read_line_stats.pop(0)
      if line.startswith(cpu):
        read_stats = line.strip().split()
        read_line_stats = []
    #endwhile

    stats = {}
    for key, pos in self.__cpu_mapping__.items():
      stats[key] = int(read_stats[pos])

    return stats
  #__read_cpustats__

  def __read_diskstat__(self, fd):
    fd.seek(0)
    read_stats = fd.read(1024).strip().split()

    stats = {}
    for key, pos in self.__disk_mapping__.items():
      stats[key] = float(read_stats[pos])

    return stats
  #__read_diskstat__

  def __value__(self, v):
    """
      param: v  tuple(previous, current)

      return: int value in bytes
    """
    iop, ioc = v
    return ((ioc * self.sector_size) - (iop * self.sector_size)) / self.interval
  #__value__
#class IOStats
