# -*- coding: utf-8 -*-
# aiomysqldb.py
# Copyright (C) 2020 KunoiSayami
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
import asyncio
import logging
import time
from configparser import ConfigParser
from threading import Thread
from typing import Iterable, NoReturn, Optional, Tuple

import aiomysql


class _mysqldb:

	def __init__(
		self,
		host: str,
		user: str,
		password: str,
		db: str,
		#event_loop: asyncio.AbstractEventLoop,
		charset: str='utf8mb4',
		cursorclass: aiomysql.Cursor=aiomysql.DictCursor,
		autocommit: bool=False
	):
		self.logger = logging.getLogger(__name__)
		self.logger.setLevel(logging.DEBUG)
		self.host = host
		self.user = user
		self.password = password
		self.db = db
		self.charset = charset
		self.cursorclass = cursorclass
		self.execute_lock = asyncio.Lock()
		self.last_execute_time = 0
		self.exit_request = False
		self.autocommit = autocommit
		self.cursor = None
		#self.retries = 3
		#self.event_loop = None
		#self.init_connection()
		self.mysql_connection = None
		self._keep_alive_task = None

	async def init_connection(self) -> NoReturn:
		self.mysql_connection = await aiomysql.connect(
			host=self.host,
			user=self.user,
			password=self.password,
			db=self.db,
			charset=self.charset,
			cursorclass=self.cursorclass,
			autocommit=self.autocommit,
			#loop=self.event_loop
		)
		self.cursor = await self.mysql_connection.cursor()

	async def commit(self) -> NoReturn:
		async with self.execute_lock:
		#async with self.execute_lock:
			await self.cursor.close()
			await self.mysql_connection.commit()
			self.cursor = await self.mysql_connection.cursor()

	async def query(self, sql: str, args: Iterable=()) -> Tuple[dict]:
		async with self.execute_lock:
			await self.execute(sql, args)
			return await self.cursor.fetchall()

	async def query1(self, sql: str, args: Iterable=()) -> Optional[dict]:
		async with self.execute_lock:
			await self.execute(sql, args)
			return await self.cursor.fetchone()

	async def execute(self, sql: str, args: tuple or list = (), many: bool = False) -> NoReturn:
		await (self.cursor.executemany if many else self.cursor.execute)(sql, args)

	async def ping(self) -> '_mysqldb':
		await self.mysql_connection.ping()
		return self

	def do_keepalive(self) -> NoReturn:
		thread = ThreadWithEventLoop()
		time.sleep(1)
		task = self._do_keepalive()
		#thread.event_loop.run_forever()
		#print(thread.event_loop.is_running())
		asyncio.run_coroutine_threadsafe(task, thread.event_loop)

	def create_keep_alive(self) -> NoReturn:
		_eventloop = asyncio.new_event_loop()
		asyncio.ensure_future(self._do_keepalive(), loop=_eventloop)
		_eventloop.run_forever()

	async def _do_keepalive(self) -> NoReturn:
		while True:
			try:
				if time.time() - self.last_execute_time > 300 and not self.exit_request:
					await self.ping()
				self.last_execute_time = time.time()
			finally:
				await asyncio.sleep(1)

	async def close(self) -> NoReturn:
		#with self.lo
		async with self.execute_lock:
			#self.exit_request = True
			await self.cursor.close()
			await self.mysql_connection.commit()
			self.mysql_connection.close()

	#async def connect(self, event_loop: asyncio.AbstractEventLoop):
	#	#self.event_loop = event_loop
	#	await self.init_connection()

class mysqldb(_mysqldb):
	_self = None
	@staticmethod
	def init_instance(
		host: str,
		user: str,
		password: str,
		db: str,
		#event_loop: asyncio.AbstractEventLoop,
		charset: str = 'utf8mb4',
		cursorclass = aiomysql.DictCursor,
		autocommit = False
	) -> _mysqldb:
		mysqldb._self = _mysqldb(host, user, password, db, charset, cursorclass, autocommit)
		return mysqldb._self
	
	@staticmethod
	def get_instance() -> _mysqldb:
		return mysqldb._self

async def main():
	config = ConfigParser()
	config.read('config.ini')
	conn = mysqldb.init_instance(config.get('mysql', 'host'),
								config.get('mysql', 'user'),
								config.get('mysql', 'password'),
								config.get('mysql', 'db'),
								autocommit=True)
	await conn.init_connection()
	obj = await conn.query1('SELECT 10;')
	print(obj)
	conn.do_keepalive()
	time.sleep(60)
	await conn.close()


class ThreadWithEventLoop(Thread):
	def __init__(self):
		super().__init__(daemon=True)
		self.event_loop = None
		#self.coro = coro
		self.start()
	def run(self):
		self.event_loop = asyncio.new_event_loop()
		self.event_loop.run_forever()

if __name__ == "__main__":
	cron = main()
	asyncio.run(cron)
	#asyncio.wait(cron)
