# -*- coding: utf-8 -*-
# Encrypt.py
# Copyright (C) 2018-2021 KunoiSayami
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
import hashlib
import os
import struct
import tempfile
from base64 import b64decode, b64encode
from configparser import ConfigParser
from typing import Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class AESGCMEncryptClassic:
	def __init__(self, key: Optional[str]=None, associated_data: Optional[str]=None, config_file: str='config.ini', *, hash_func=hashlib.sha256):
		config = ConfigParser()
		if not all((key, associated_data)):
			# Try read data from configure file
			if len(config.read(config_file)) == 0 or not config.has_section('encrypt'):
				raise IOError(f'`{config_file}\' is not a compliant profile.')
		#self.key = key if key else config['encrypt']['key']
		self.key: bytes = hash_func((key if key else config['encrypt']['key']).encode()).digest()
		self.associated_data: bytes = (associated_data if associated_data else config['encrypt']['associated_data']).encode()

	@staticmethod
	def _encrypt(key: bytes, plaintext: bytes, associated_data: bytes) -> Tuple[bytes, bytes, bytes]:
		# Generate a random 96-bit IV.
		iv = os.urandom(12)

		# Construct an AES-GCM Cipher object with the given key and a
		# randomly generated IV.
		encryptor = Cipher(
			algorithms.AES(key),
			modes.GCM(iv),
			backend=default_backend()
		).encryptor()

		# associated_data will be authenticated but not encrypted,
		# it must also be passed in on decryption.
		encryptor.authenticate_additional_data(associated_data)

		# Encrypt the plaintext and get the associated ciphertext.
		# GCM does not require padding.
		ciphertext = encryptor.update(plaintext) + encryptor.finalize()

		return (iv, ciphertext, encryptor.tag)

	@staticmethod
	def _decrypt(key: bytes, associated_data: bytes, iv: bytes, ciphertext: bytes, tag: bytes) -> bytes:
		# Construct a Cipher object, with the key, iv, and additionally the
		# GCM tag used for authenticating the message.
		decryptor = Cipher(
			algorithms.AES(key),
			modes.GCM(iv, tag),
			backend=default_backend()
		).decryptor()

		# We put associated_data back in or the tag will fail to verify
		# when we finalize the decryptor.
		decryptor.authenticate_additional_data(associated_data)

		# Decryption gets us the authenticated plaintext.
		# If the tag does not match an InvalidTag exception will be raised.
		return decryptor.update(ciphertext) + decryptor.finalize()

	def encrypts(self, plaintext: str) -> Tuple[bytes, bytes, bytes]:
		return self.encrypt(plaintext.encode())

	def encrypt(self, binary_str: bytes) -> Tuple[bytes, bytes, bytes]:
		'''
			return (iv, ciphertext, encryptor.tag)
		'''
		return self._encrypt(self.key, binary_str, self.associated_data)

	def b64encrypt(self, binary_str: bytes) -> str:
		return '\\\\n'.join((b64encode(_str).decode() for _str in self.encrypt(binary_str)))

	def b64encrypts(self, plaintext: str) -> str:
		return self.b64encrypt(plaintext.encode())

	def decrypt(self, iv: bytes, ciphertext: bytes, tag: bytes) -> bytes:
		return self._decrypt(self.key, self.associated_data, iv, ciphertext, tag)

	def decrypts(self, iv: bytes, ciphertext: bytes, tag: bytes) -> str:
		return self.decrypt(iv, ciphertext, tag).decode()

	def b64decrypt(self, base64_encoded_str: bytes) -> bytes:
		return self.decrypt(*(b64decode(_str.encode()) for _str in base64_encoded_str.decode().split('\\\\n')))

	def b64decrypts(self, base64_encoded_str: bytes) -> str:
		return self.b64decrypt(base64_encoded_str).decode()


class AESGCMEncrypt(AESGCMEncryptClassic):
	VERSION = 1

	class VersionException(Exception):
		"""When version mismatch raise"""

	@staticmethod
	def encrypt_file(key: bytes, input_file_name: str, output_file_name: str,
					 associated_data: bytes, chunk_size: int = 1024) -> None:
		# Generate a random 96-bit IV.
		iv = os.urandom(12)

		# Construct an AES-GCM Cipher object with the given key and a
		# randomly generated IV.
		encryptor = Cipher(
			algorithms.AES(key),
			modes.GCM(iv),
			backend=default_backend()
		).encryptor()

		# associated_data will be authenticated but not encrypted,
		# it must also be passed in on decryption.
		encryptor.authenticate_additional_data(associated_data)

		with open(input_file_name, 'rb') as fin, open(output_file_name, 'wb') as fout:
			fout.write(struct.pack('<Q12s16s', AESGCMEncrypt.VERSION, iv, b''))
			while True:
				chunk = fin.read(chunk_size)
				if len(chunk) == 0:
					break
				fout.write(encryptor.update(chunk))
			fout.write(encryptor.finalize())
			fout.seek(struct.calcsize('Q12s'))
			fout.write(struct.pack('16s', encryptor.tag))
			#print(AESGCMEncrypt.VERSION, iv, encryptor.tag)

	@staticmethod
	def decrypt_file(key: bytes, input_file_name: str, output_file_name: str, associated_data: bytes, chunk_size: int = 1024) -> None:
		with open(input_file_name, 'rb') as fin, open(output_file_name, 'wb') as fout:
			#associated_data_size, tag_size = struct.unpack('<QQ', fin.read(struct.calcsize('QQ')))
			_version, iv, tag = struct.unpack('<Q12s16s', fin.read(struct.calcsize('Q12s16s')))
			#print(_version, iv, tag)
			#associated_data = fin.read(associated_data_size)
			if _version != AESGCMEncrypt.VERSION:
				raise AESGCMEncrypt.VersionException(f'Except {AESGCMEncrypt.VERSION} but {_version} found.')
			decryptor = Cipher(
				algorithms.AES(key),
				modes.GCM(iv, tag),
				backend=default_backend()
			).decryptor()
			decryptor.authenticate_additional_data(associated_data)
			#reader = lib_aes_gcm.chunk_reader(fin, file_size)
			while True:
				chunk = fin.read(chunk_size)
				if len(chunk) == 0:
					break
				fout.write(decryptor.update(chunk))
			fout.write(decryptor.finalize())

	def fencrypt(self, input_file_name: str, output_file_name: str, chunk_size: int = 1024) -> None:
		self.encrypt_file(self.key, input_file_name, output_file_name, self.associated_data, chunk_size)

	def fdecrypt(self, input_file_name: str, output_file_name: str, chunk_size: int = 1024) -> None:
		self.decrypt_file(self.key, input_file_name, output_file_name, self.associated_data, chunk_size)


def test_random_file(mute: bool = False) -> None:
	import random
	interrupted = False
	with tempfile.TemporaryDirectory(prefix='tmp', dir='.') as tmpd:
		os.chdir(tmpd)
		try:
			with open('origin.txt', 'wb') as fout:
				for _ in range(100000):
					fout.write(chr(ord('A') + random.randint(0, 23)).encode())
			test_specify_file('origin.txt', mute)
		except InterruptedError:
			interrupted = True
		os.chdir('..')
	if interrupted:
		raise InterruptedError


def test_specify_file(file_name: str, mute: bool = False) -> None:
	import filecmp, traceback
	key = b'test'
	key_hash = hashlib.sha256(key).digest()
	try:
		AESGCMEncrypt.encrypt_file(key_hash, file_name, file_name + '.enc', b'data')
		AESGCMEncrypt.decrypt_file(key_hash, file_name + '.enc', 'decrypted.txt', b'data')
		if mute is not True and filecmp.cmp(file_name, 'decrypted.txt'):
			print('File test successfully')
	except (TypeError, ValueError):
		traceback.print_exc()


if __name__ == '__main__':
	s = AESGCMEncryptClassic('1234', 'associated data')
	print(s.b64decrypts(s.b64encrypts('This is test string').encode()))
	test_random_file()
