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
from typing import Dict, Optional, Sequence, TypeVar, Tuple, Union, ByteString

import aiomysql

_cT = TypeVar('_cT', str, int, None, ByteString)

class MySqlDB:

	_self: Optional['MySqlDB'] = None

	def __init__(
		self,
		host: str,
		user: str,
		password: str,
		db: str,
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
		self.mysql_pool: aiomysql.Connection = None

	async def init_connection(self) -> None:
		self.mysql_pool = await aiomysql.create_pool(
			host=self.host,
			user=self.user,
			password=self.password,
			db=self.db,
			charset=self.charset,
			cursorclass=self.cursorclass,
			autocommit=True
		)

	async def query(self, sql: str, args: Union[Sequence[_cT], _cT]=()) -> Tuple[Dict[str, _cT]]:
		async with self.mysql_pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(sql, args)
				return await cur.fetchall()

	async def query1(self, sql: str, args: Union[Sequence[_cT], _cT]=()) -> Optional[Dict[str, _cT]]:
		async with self.mysql_pool.acquire() as conn:
			async with conn.cursor() as cur:
				await cur.execute(sql, args)
				return await cur.fetchone()

	async def execute(self, sql: str, args: Union[Sequence[_cT], Sequence[Sequence[_cT]]]=(), many: bool=False) -> None:
		async with self.mysql_pool.acquire() as conn:
			async with conn.cursor() as cur:
				await (cur.executemany if many else cur.execute)(sql, args)
			await conn.commit()

	async def close(self) -> None:
		self.mysql_pool.close()
		await self.mysql_pool.wait_closed()

	@classmethod
	async def create(cls,
		host: str,
		user: str,
		password: str,
		db: str,
		charset: str='utf8mb4',
		cursorclass: aiomysql.Cursor=aiomysql.DictCursor
	):
		self = cls(host, user, password, db, charset, cursorclass)
		if cls._self is None:
			cls._self = self
		await self.init_connection()
		return self

	@staticmethod
	def get_instance() -> 'MySqlDB':
		if MySqlDB._self is None:
			raise RuntimeError()
		return MySqlDB._self

async def main() -> None:
	config = ConfigParser()
	config.read('config.ini')
	conn = await MySqlDB.create(config.get('mysql', 'host'),
								config.get('mysql', 'user'),
								config.get('mysql', 'password'),
								config.get('mysql', 'db'))
	await conn.init_connection()
	obj = await conn.query1('SELECT 10;')
	print(obj)
	#conn.do_keepalive()
	await conn.close()

if __name__ == "__main__":
	cron = main()
	asyncio.run(cron)
	#asyncio.wait(cron)
