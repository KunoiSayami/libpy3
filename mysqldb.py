# -*- coding: utf-8 -*-
# Log.py
# Copyright (C) 2018-2019 KunoiSayami
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

class mysqldb(object):

	def __init__(
		self,
		host: str,
		user: str,
		password: str,
		db: str,
		charset: str = 'utf8mb4',
		cursorclass = pymysql.cursors.DictCursor
	):
		self.host = host
		self.user = user
		self.password = password
		self.db = db
		self.charset = charset
		self.cursorclass = cursorclass
		self.lock = Lock()
		self.init_connection()

	def init_connection(self):
		self.mysql_connection = pymysql.connect(
			host = self.host,
			user = self.user,
			password = self.password,
			db = self.db,
			charset = self.charset,
			cursorclass = self.cursorclass
		)
		self.cursor = self.mysql_connection.cursor()

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
			try:
				self.cursor.execute(sql, args)
			except pymysql.err.OperationalError as e:
				import traceback, sys
				err = traceback.format_exc().splitlines()[-1]
				if '2006' in err:
					try:
						self.mysql_connection.close()
					except:
						pass
					self.init_connection()
				else:
					traceback.print_exc(file=sys.stderr)
					raise e

	def ping(self):
		return self.mysql_connection.ping()

	def close(self):
		with self.lock:
			self.cursor.close()
			self.mysql_connection.commit()
