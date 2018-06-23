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
import pymysql.cursors
from threading import Lock

class mysqldb:
	def __init__(self, host, user, password, db, charset='utf8', cursorclass=pymysql.cursors.DictCursor):
		self.mysql_connection = pymysql.connect(host=host, user=user, password=password, db=db, charset=charset, cursorclass=cursorclass)
		self.cursor = self.mysql_connection.cursor()
		self.lock = Lock()
	def commit(self):
		with self.lock:
			self.cursor.close()
			self.mysql_connection.commit()
			self.cursor = self.mysql_connection.cursor()
	def query(self, sql, args=()):
		self.execute(sql, args)
		return self.cursor.fetchall()
	def query1(self, sql, args=()):
		self.execute(sql, args)
		return self.cursor.fetchone()
	def execute(self, sql, args=()):
		with self.lock:
			self.cursor.execute(sql, args)
	def close(self):
		with self.lock:
			self.cursor.close()
			self.mysql_connection.commit()