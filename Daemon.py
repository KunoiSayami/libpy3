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
import time

class DaemonThread(Thread):
	def __init__(self, target_func=None, *args, **kwargs):
		Thread.__init__(self)
		self.daemon = True
		self.target_func = target_func
		self.args = args
		self.kwargs = kwargs
		self.start()
	def run(self):
		if self.target_func is None:
			raise NotImplementedError('The subclass of `DaemonThread` should implement `run()\'')
		else:
			self.target_func(*self.args, **self.kwargs)

class TimerDaemonThread:
	def __init__(self, timer: int, target_func=None, *args, **kwargs):
		self._t = Thread(target=(target_func if target_func is not None else self.run), args=args, kwargs=kwargs, daemon=True)
		self.timer = timer
	def start(self):
		time.sleep(self.timer)
		self._t.start()
	def isAlive(self):
		return self._t.isAlive()
	def join(self, timeout=None):
		self._t.join(timeout)
	def run(self):
		raise NotImplementedError('The subclass of `DaemonThread` should implement `run()\'')
