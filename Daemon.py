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
import subprocess

class DaemonProcessError(Exception): pass

'''
; in `config.ini`
[daemon]
custom_startup = python3
slice = True
'''

class DaemonProcess(object):
	def __init__(self, main_entry_function,
		help_function = None,
		custom_arg: tuple or list = ('-d', '--daemon'),
		*,
		need_config_file: bool = False,
		config_file_name: str = 'config.ini',
		config_section: str = 'daemon',
		custom_end_function = None):
		def __call_help(help_func):
			if help_func is not None: help_func()
		if len(sys.argv) == 2:
			if sys.argv[1] in custom_arg:
				if need_config_file:
					try:
						from configparser import ConfigParser
						config = ConfigParser()
						if len(config.read(config_file_name)) == 0:
							raise ValueError
						custom_startup = config[config_section]['custom_startup'] if config.has_option(config_section, 'custom_startup') else sys.executable
						nohup = config[config_section]['slice'] if config.has_option(config_section, 'slice') else True
					except:
						nohup = True
						custom_startup = sys.executable
				else:
					nohup = True
					custom_startup = sys.executable
				subprocess.Popen([custom_startup, sys.argv[0], '--daemon-start'], stdout=subprocess.DEVNULL if nohup else None)
			elif sys.argv[1] in '--daemon-start':
				with open('.pid', 'w') as fout:
					fout.write(str(os.getpid()))
				custom_end_function = None
			elif sys.argv[1] in ('--kill', '--exit', '-k'):
				import signal
				with open('.pid') as fin:
					os.kill(int(fin.read()), signal.SIGINT)
				if custom_end_function: custom_end_function()
			else:
				__call_help(help_function)
		else:
			__call_help(help_function)
