import struct
from os import SEEK_CUR
from typing import IO, Union
from io import FileIO

FileLike = Union[IO[bytes], FileIO]


def read(fp: FileLike, format_str: str):
    """read data from `fp` specified by `format_str`"""
    num_bytes = struct.calcsize(format_str)
    byts = fp.read(num_bytes)
    ans = struct.unpack(format_str, byts)
    return ans if len(ans) > 1 else ans[0]


def skip(fp: FileLike, n: int):
    """skip `n` bytes in `fp`"""
    fp.seek(n, SEEK_CUR)


def write(fp: FileLike, format_str: str, items: tuple):
    """write to `fp`, `items` specified by `format_str`"""
    pack = struct.pack(format_str, *items)
    fp.write(pack)
