# -*- coding: utf-8 -*-
# aiopgsqldb.py
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
import asyncpg

from typing import Optional, Tuple, Union, Sequence, Any


class PgSQLdb:

    def __init__(
            self,
            host: str,
            port: int,
            user: str,
            password: str,
            db: str,
    ):
        self.host: str = host
        self.port: int = port
        self.user: str = user
        self.password: str = password
        self.db: str = db
        self.pgsql_connection: asyncpg.connection = None

    async def create_connect(self) -> None:
        self.pgsql_connection = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db
        )

    @classmethod
    async def create(cls,
                     host: str,
                     port: int,
                     user: str,
                     password: str,
                     db: str,
                     ) -> 'PgSQLdb':
        self = cls(host, port, user, password, db)
        await self.create_connect()
        return self

    async def query(self, sql: str, *args: Optional[Any]) -> Tuple[asyncpg.Record, ...]:
        return await self.pgsql_connection.fetch(sql, *args)

    async def query1(self, sql: str, *args: Optional[Any]) -> Optional[asyncpg.Record]:
        return await self.pgsql_connection.fetchrow(sql, *args)

    async def execute(self, sql: str, *args: Union[Sequence[Tuple[Any, ...]],
                                                   Optional[Any]], many: bool = False) -> None:
        if many:
            await self.pgsql_connection.executemany(sql, *args)
        else:
            await self.pgsql_connection.execute(sql, *args)

    async def close(self) -> None:
        await self.pgsql_connection.close()
