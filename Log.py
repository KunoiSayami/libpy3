# -*- coding: utf-8 -*-
# Log.py
# Copyright (C) 2018 Too-Naive
#
# This module is part of libpy3 and is released under
# the AGPL v3 License: https://www.gnu.org/licenses/agpl-3.0.txt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
from queue import Queue
from threading import Lock
from configparser import ConfigParser
import inspect, time, traceback, sys, os

'''
;config.ini
[log]
; OFF/EMERG/CRIT/FATAL/ALERT/ERROR/WARN/NOTIFY/INFO/DEBUG/ALL
log_level = 
; Absolute path or relative path
log_file = 
; Absolute path or relative path also (stderr/stdout/None)
pre_print =
; Use queue to store emergency log (bool: default = true)
use_queue =
; Print to sth when reach specified level
emerg_print =
; Specify print to standard pipe (stderr/stdout)
emerg_print_to =
'''

__currentcwdlen = len(os.getcwd()) + 1

global LOG_QUEUE_OPTION, LOG_EMERG_PRINT, LOG_EMERG_PRINT_TO

LOG_LOCK = Lock()
LOG_LEVEL_LIST = ['OFF', 'EMERG', 'CRIT', 'FATAL', 'ERROR', 'ALERT', 'WARN', 'NOTIFY', 'INFO', 'DEBUG', 'ALL']

def __init_emerg_print(config: ConfigParser):
	global LOG_EMERG_PRINT, LOG_EMERG_PRINT_TO
	if config.has_option('log', 'emerg_print') and config['log']['emerg_print'] in LOG_LEVEL_LIST[1:]:
		assert config.has_option('log', 'emerg_print_to') and config['log']['emerg_print_to'] in ('stderr', 'stdout')
		LOG_EMERG_PRINT = LOG_LEVEL_LIST.index(config['log']['emerg_print'])
		LOG_EMERG_PRINT_TO = {'stderr': sys.stderr, 'stdout': sys.stdout}[config['log']['emerg_print_to']]
	else:
		LOG_EMERG_PRINT = False
		LOG_EMERG_PRINT_TO = None

def init_log():
	global LOG_QUEUE_OPTION
	def _get_target(target):
		try:
			return {'stderr': sys.stderr, 'stdout': sys.stdout, 'None': None}[target]
		except KeyError:
			return open(target, 'a')
	config = ConfigParser()
	config.read('config.ini')
	__init_emerg_print(config)
	LOG_QUEUE_OPTION = not (config.has_option('log', 'use_queue') and config['log']['use_queue'] == 'false')
	return config['log']['log_level'], open(config['log']['log_file'], 'a'), _get_target(config['log']['pre_print'])

class __useless_queue:
	@staticmethod
	def put(_): pass
	@staticmethod
	def get(_): raise NotImplementedError

LOG_LEVEL_DICT = {LOG_LEVEL_LIST[x]:x  for x in range(len(LOG_LEVEL_LIST))}
LOG_LEVEL, LOG_FILE, LOG_PRE_PRINT = init_log()
LOG_QUEUE = Queue() if LOG_QUEUE_OPTION else __useless_queue()

def get_func_name():
	currentFrame = inspect.currentframe()
	outerFrame = inspect.getouterframes(currentFrame)
	returnStr = '{}.{}][{}'.format(outerFrame[3][1][__currentcwdlen:-3].replace('\\','.').replace('/','.'),
		outerFrame[3][3], outerFrame[3][2])
	del outerFrame
	del currentFrame
	return returnStr[1:] if returnStr[0] == '.' else returnStr

def reopen():
	global LOG_FILE, LOG_PRE_PRINT, LOG_LEVEL
	LOG_FILE.close()
	if LOG_PRE_PRINT not in (sys.stderr, sys.stdout, None):
		LOG_PRE_PRINT.close()
	LOG_LEVEL, LOG_FILE, LOG_PRE_PRINT = init_log()

def get_level(level: str):
	return LOG_LEVEL_LIST.index(level) if level in LOG_LEVEL_LIST else LOG_LEVEL_LIST.index('ALL')

def log(log_level: str, s: str, start: str = '', end: str = '\n', pre_print: bool = True, need_put_queue: bool = True):
	global LOG_LOCK, LOG_PRE_PRINT, LOG_QUEUE, LOG_FILE
	log_text = '{}[{}] [{}]\t[{}] {}{}'.format(start, time.strftime('%Y-%m-%d %H:%M:%S'),
		log_level, get_func_name(), s, end)
	if log_level in LOG_LEVEL_LIST[1:] and LOG_LEVEL_LIST.index(log_level) < 4:
	#if  0 < LOG_LEVEL_DICT.get(log_level, LOG_LEVEL_DICT['ALL']) < 4:
		LOG_QUEUE.put(log_text)
	log_level_num = get_level(log_level)
	LOG_LOCK.acquire()
	try:
		if LOG_EMERG_PRINT and LOG_EMERG_PRINT >= log_level_num:
			LOG_EMERG_PRINT_TO.write(log_text)
			LOG_EMERG_PRINT_TO.flush()
		if pre_print and LOG_PRE_PRINT:
			LOG_PRE_PRINT.write(log_text)
			LOG_PRE_PRINT.flush()
		if ((log_level in LOG_LEVEL_LIST and LOG_LEVEL_LIST.index(log_level) <= LOG_LEVEL_LIST.index(LOG_LEVEL)) or \
			(log_level not in LOG_LEVEL_LIST and LOG_LEVEL == 'ALL')) and LOG_FILE:
			LOG_FILE.write(log_text)
			LOG_FILE.flush()
	except:
		traceback.print_exc()
	finally:
		LOG_LOCK.release()

def emerg(fmt: tuple or list, *args, **kwargs):
	log('EMERG', fmt.format(*args), **kwargs)

def fatal(fmt: tuple or list, *args, **kwargs):
	log('FATAL', fmt.format(*args), **kwargs)

def crit(fmt: tuple or list, *args, **kwargs):
	log('CRIT', fmt.format(*args), **kwargs)

def error(fmt: tuple or list, *args, **kwargs):
	log('ERROR', fmt.format(*args), **kwargs)

def alert(fmt: tuple or list, *args, **kwargs):
	log('ALERT', fmt.format(*args), **kwargs)

def warn(fmt: tuple or list, *args, **kwargs):
	log('WARN', fmt.format(*args), **kwargs)

def notify(fmt: tuple or list, *args, **kwargs):
	log('NOTIFY', fmt.format(*args), **kwargs)

def info(fmt: tuple or list, *args, **kwargs):
	log('INFO', fmt.format(*args), **kwargs)

def custom(level: str, fmt: tuple or list, *args, **kwargs):
	log(level, fmt.format(*args), **kwargs)

def exc(pre_print: bool = True):
	log('ERROR', '\n{}'.format(traceback.format_exc()), pre_print=pre_print)
