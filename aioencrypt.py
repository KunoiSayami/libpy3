# -*- coding: utf-8 -*-
# aioencrypt.py
# Copyright (C) 2020-2021 KunoiSayami
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
#
# origin from https://goo.gl/8PToR6
import asyncio
import hashlib
import os
import struct
import tempfile

import aiofiles
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from Encrypt import AESGCMEncryptClassic


class AESGCMEncrypt(AESGCMEncryptClassic):
    VERSION = 1
    CHUNK_SIZE = 1024 * 8

    class VersionException(Exception):
        """When version mismatch raise"""

    @staticmethod
    async def encrypt_file(key: bytes, input_file_name: str, output_file_name: str, associated_data: bytes,
                           chunk_size: int = CHUNK_SIZE) -> None:
        # Generate a random 96-bit IV.
        iv = os.urandom(12)

        # Construct an AES-GCM Cipher object with the given key and a
        # randomly generated IV.
        encryptor = Cipher(
            algorithms.AES(key),  # type: ignore
            modes.GCM(iv),  # type: ignore
            backend=default_backend()
        ).encryptor()

        # associated_data will be authenticated but not encrypted,
        # it must also be passed in on decryption.
        encryptor.authenticate_additional_data(associated_data)  # type: ignore

        async with aiofiles.open(input_file_name, 'rb') as fin, aiofiles.open(output_file_name, 'wb') as fout:
            await fout.write(struct.pack('<Q12s16s', AESGCMEncrypt.VERSION, iv, b''))
            while chunk := await fin.read(chunk_size):
                await fout.write(encryptor.update(chunk))
            await fout.write(encryptor.finalize())
            await fout.seek(struct.calcsize('Q12s'))
            await fout.write(struct.pack('16s', encryptor.tag))  # type: ignore

    @staticmethod
    async def decrypt_file(key: bytes, input_file_name: str, output_file_name: str, associated_data: bytes,
                           chunk_size: int = CHUNK_SIZE) -> None:
        async with aiofiles.open(input_file_name, 'rb') as fin, aiofiles.open(output_file_name, 'wb') as fout:
            _version, iv, tag = struct.unpack('<Q12s16s', await fin.read(struct.calcsize('Q12s16s')))
            if _version != AESGCMEncrypt.VERSION:
                raise AESGCMEncrypt.VersionException(f'Except {AESGCMEncrypt.VERSION} but {_version} found.')
            decryptor = Cipher(
                algorithms.AES(key),  # type: ignore
                modes.GCM(iv, tag),  # type: ignore
                backend=default_backend()
            ).decryptor()
            decryptor.authenticate_additional_data(associated_data)  # type: ignore
            # reader = lib_aes_gcm.chunk_reader(fin, file_size)
            while chunk := await fin.read(chunk_size):
                await fout.write(decryptor.update(chunk))
            await fout.write(decryptor.finalize())

    async def fencrypt(self, input_file_name: str, output_file_name: str, chunk_size: int = CHUNK_SIZE) -> None:
        await self.encrypt_file(self.key, input_file_name, output_file_name, self.associated_data, chunk_size)

    async def fdecrypt(self, input_file_name: str, output_file_name: str, chunk_size: int = CHUNK_SIZE) -> None:
        await self.decrypt_file(self.key, input_file_name, output_file_name, self.associated_data, chunk_size)


async def test_random_file(mute: bool = False) -> None:
    interrupted = False
    with tempfile.TemporaryDirectory(prefix='tmp', dir='.') as tmpd:
        os.chdir(tmpd)
        try:
            async with aiofiles.open('origin.txt', 'wb') as fout:
                for _ in range(10000):
                    await fout.write(''.join(chr(ord('A') + random.randint(0, 23)) for _x in range(100)).encode())
            await test_specify_file('origin.txt', mute)
        except InterruptedError:
            interrupted = True
        os.chdir('..')
    if interrupted:
        raise InterruptedError


async def test_specify_file(file_name: str, mute: bool = False) -> None:
    key = b'test'
    key_hash = hashlib.sha256(key).digest()
    try:
        await AESGCMEncrypt.encrypt_file(key_hash, file_name, file_name + '.enc', b'data')
        await AESGCMEncrypt.decrypt_file(key_hash, file_name + '.enc', 'decrypted.txt', b'data')
        if mute is not True and filecmp.cmp(file_name, 'decrypted.txt'):
            print('File test successfully')
    except (TypeError, ValueError):
        traceback.print_exc()


if __name__ == '__main__':
    import filecmp, traceback, random
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_random_file())
