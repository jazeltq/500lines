# This started as a very thin wrapper around a file object, with intent to
# provide an object address on write() and a superblock. But as I was writing
# it, I realised that the user really wouldn't want to deal with the lengths of
# the writen chunks (and Pickle won't do it for you), so this module would have
# to abstract the file object into it's own degenerate key/value store.
# (Degenerate because you can't pick the keys, and it never releases storage,
# even when it becomes unreachable!)

import os
import struct


class Storage(object):
    SUPERBLOCK_SIZE = 4096
    INTEGER_FORMAT = "!Q"
    INTEGER_LENGTH = 8

    def __init__(self, f):
        self._f = f
        self._ensure_superblock()

    def _ensure_superblock(self):
        self._seek_end()
        end_address = self._f.tell()
        if end_address < self.SUPERBLOCK_SIZE:
            self._f.write('\x00' * (self.SUPERBLOCK_SIZE - end_address))

    def _seek_end(self):
        self._f.seek(0, os.SEEK_END)

    def _seek_superblock(self):
        self._f.seek(0)

    def _bytes_to_integer(self, integer_bytes):
        return struct.unpack(self.INTEGER_FORMAT, integer_bytes)[0]

    def _integer_to_bytes(self, integer):
        return struct.pack(self.INTEGER_FORMAT, integer)

    def _read_integer(self):
        return self._bytes_to_integer(self._f.read(self.INTEGER_LENGTH))

    def _write_integer(self, integer):
        self._f.write(self._integer_to_bytes(integer))

    def write(self, data):
        self._seek_end()
        object_address = self._f.tell()
        self._write_integer(len(data))
        self._f.write(data)
        return object_address

    def read(self, address):
        self._f.seek(address)
        length = self._read_integer()
        data = self._f.read(length)
        return data

    def commit_root_address(self, root_address):
        self._f.flush()
        self._seek_superblock()
        self._write_integer(root_address)
        self._f.flush()

    def get_root_address(self):
        self._seek_superblock()
        root_address = self._read_integer()
        return root_address

    def close(self):
        self._f.close()
