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
from configparser import ConfigParser
from threading import Thread
from typing import Dict, NoReturn, Optional, Sequence, T, Tuple, Union

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
	):
		self.logger: logging.Logger = logging.getLogger(__name__)
		self.logger.setLevel(logging.DEBUG)
		self.host: str = host
		self.user: str = user
		self.password: str = password
		self.db: str = db
		self.charset: str = charset
		self.cursorclass: aiomysql.Cursor = cursorclass
		self.execute_lock: asyncio.Lock = asyncio.Lock()
		self.last_execute_time: float = 0.0
		self.exit_request: bool = False
		self.autocommit: bool = True
		#self.cursor = None
		#self.retries = 3
		#self.event_loop = None
		#self.init_connection()
		#self.mysql_connection = None
		self.mysql_pool: aiomysql.Connection = None
		#self._keep_alive_task = None

	async def init_connection(self) -> NoReturn:
		self.mysql_pool = await aiomysql.create_pool(
			host=self.host,
			user=self.user,
			password=self.password,
			db=self.db,
			charset=self.charset,
			cursorclass=self.cursorclass,
			autocommit=True,
			#loop=self.event_loop
		)
		#self.cursor = await self.mysql_connection.cursor()

	@classmethod
	async def create(cls,
		host: str,
		user: str,
		password: str,
		db: str,
		charset: str='utf8mb4',
		cursorclass: aiomysql.Cursor=aiomysql.DictCursor
	) -> '_mysqldb':
		self = _mysqldb(host, user, password, db, charset, cursorclass)
		await self.init_connection()
		return self

	async def query(self, sql: str, args: Sequence[str]=()) -> Tuple[Dict[str, T]]:
		async with self.mysql_pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(sql, args)
				return await cur.fetchall()

	async def query1(self, sql: str, args: Sequence[str]=()) -> Optional[Dict[str, T]]:
		async with self.mysql_pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(sql, args)
				return await cur.fetchone()

	async def execute(self, sql: str, args: Union[Sequence[str], Sequence[Sequence[str]]]=(), many: bool=False) -> NoReturn:
		#await self.reconnect_check()
		async with self.mysql_pool.acquire() as conn:
			async with conn.cursor() as cur:
				await (cur.executemany if many else cur.execute)(sql, args)
			await conn.commit()
		#self.last_execute_time = time.time()

	async def close(self) -> NoReturn:
		self.mysql_pool.close()
		await self.mysql_pool.wait_closed()

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
	) -> _mysqldb:
		mysqldb._self = _mysqldb(host, user, password, db, charset, cursorclass)
		return mysqldb._self
	
	@classmethod
	async def create(cls,
		host: str,
		user: str,
		password: str,
		db: str,
		charset: str='utf8mb4',
		cursorclass: aiomysql.Cursor=aiomysql.DictCursor
	) -> 'mysqldb':
		self = mysqldb(host, user, password, db, charset, cursorclass)
		mysqldb._self = self
		await self.init_connection()
		return self

	@staticmethod
	def get_instance() -> _mysqldb:
		return mysqldb._self

async def main():
	config = ConfigParser()
	config.read('config.ini')
	conn = mysqldb.init_instance(config.get('mysql', 'host'),
								config.get('mysql', 'user'),
								config.get('mysql', 'password'),
								config.get('mysql', 'db'))
	await conn.init_connection()
	obj = await conn.query1('SELECT 10;')
	print(obj)
	#conn.do_keepalive()
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
