# -*- coding: utf-8 -*-
# Daemon.py
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
from threading import Thread
import sys, os
from subprocess import Popen

class DaemonThreadError(Exception):
	pass

class DaemonProcessError(Exception):
	pass

class DaemonThread:
	def __init__(self, target=None, args=()):
		import Log
		def __run(target, args):
			try:
				target(*args)
			except:
				Log.exc()
				raise DaemonThreadError('Daemon thread raised exception')
		self._t = Thread(target=__run, args=(target or self.run, args), daemon=True)

	def start(self):
		self._t.start()

	def join(self, timeout=None):
		self._t.join(timeout=timeout)

	def isAlive(self):
		return self._t.isAlive()

	def run(self, *args):
		raise NotImplementedError('The subclass of `DaemonThread` should implement `run()\'')

class DaemonProcess:
	def __init__(self, main_entry, help_func=None, custom_arg=('-d', '--daemon'), config_file_name='config.ini', config_section='daemon'):
		def __call_help(help_func):
			if help_func is not None:
				help_func()
		if len(sys.argv) == 2:
			if sys.argv[1] in custom_arg:
				try:
					from configparser import ConfigParser
					config = ConfigParser()
					config.read(config_file_name)
					custom_startup = config[config_section]['custom_startup']
					nohup = config[config_section]['slice']
				except:
					nohup = True
					custom_startup = 'python3'
				Popen([custom_startup, sys.argv[0], '--daemon-start' if not nohup else '--daemon-start-q'])
			elif sys.argv[1] in ('--daemon-start', '--daemon-start-q'):
				import platform
				if sys.argv[1][-1] == 'q':
					sys.stdout = open('nul' if platform.system() == 'Windows' else '/dev/null', 'w')
				with open('.pid', 'w') as fout:
					fout.write(str(os.getpid()))
				main_entry()
			elif sys.argv[1] == '-kill':
				import signal
				with open('.pid') as fin:
					os.kill(int(fin.read()), signal.SIGINT)
			else:
				__call_help(help_func)
		else:
			__call_help(help_func)
