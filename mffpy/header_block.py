"""Management of header blocks in .mff binary files

.mff binary files have a blocked structure.  Consecutive blocks can be
separated by a header, which brings us to the topic of this module.

The header consists of either a single flag (`flag=0`) or a block describing
the following bytes of signal data (`flag=1`).  Regardless, the flag is 32-bit
wide.

This module adds functionality to read and write these header blocks.

**Header block structure**

byte 0 : header flag
byte 1 : number of bytes in the header
byte 2 : number of bytes in the following data block
byte 3 : number of channels in the data block
bytes 4 to 4+nc : byte offset in the block for each signal
bytes 4+nc to 4+nc*2 : signal frequencies,word 1, and depths, word 2
bytes 4+nc*2 to `header_size` : padding

Notes
-----
The padding is a number of trash bytes which we set to match
'/examples/example_1.mff'.


Copyright 2019 Brain Electrophysiology Laboratory Company LLC

Licensed under the ApacheLicense, Version 2.0(the "License");
you may not use this module except in compliance with the License.
You may obtain a copy of the License at:

http: // www.apache.org / licenses / LICENSE - 2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
ANY KIND, either express or implied.
"""
import struct
from os import SEEK_CUR
from typing import IO, Union, Optional, Tuple
from collections import namedtuple
from io import FileIO

import numpy as np

FileLike = Union[IO[bytes], FileIO]


# Magic padding from '/examples/example_1.mff/signal1.bin', so that we survive
# the tests.  Ask Robert about this!!!
PADDING = np.array([
    24, 0, 0, 0,
    1, 0, 0, 0,
    189, 0, 0, 0,
    0, 0, 0, 0,
    196, 63, 9, 0,
    0, 0, 0, 0,
    1, 1, 0, 0],
    dtype=np.uint8).tobytes()

_HeaderBlock = namedtuple('_HeaderBlock', [
    'header_size',
    'block_size',
    'num_channels',
    'num_samples',
    'sampling_rate'
])


def read(fp: FileLike, format_str: str):
    num_bytes = struct.calcsize(format_str)
    byts = fp.read(num_bytes)
    ans = struct.unpack(format_str, byts)
    return ans if len(ans) > 1 else ans[0]


def skip(fp: FileLike, n: int):
    fp.seek(n, SEEK_CUR)


def write(fp: FileLike, format_str: str, items: tuple):
    pack = struct.pack(format_str, *items)
    fp.write(pack)


class HeaderBlock(_HeaderBlock):

    HEADER_PRESENT = 1

    def __new__(cls,
                block_size: int,
                num_channels: int,
                num_samples: int,
                sampling_rate: int,
                header_size: Optional[int] = None):
        """create new HeaderBlock instance

        Parameters
        ----------
        block_size : byte size of the block
        num_channels : channel count in the block
        num_samples : sample count per channel in the block
        sampling_rate : sampling_rate per channel in the block
        header_size : byte size of the header (computed if None)
        """
        header_size = header_size or cls.compute_byte_size(num_channels)
        return super().__new__(cls, header_size, block_size, num_channels,
                               num_samples, sampling_rate)

    @classmethod
    def from_file(cls, fp: FileLike):
        """return HeaderBlock, read from fp"""

        # Each block starts with a 4-byte-long header flag which is
        # * `0`: there is no header
        # * `1`: it follows a header
        if read(fp, 'i') == 0:
            return None
        # Read general information
        header_size, block_size, num_channels = read(fp, '3i')
        # number of 4-byte samples per channel in the data block
        num_samples = (block_size//num_channels) // 4
        # Read channel-specific information
        nc4 = 4 * num_channels
        # Skip byte offsets
        skip(fp, nc4)
        # Sample rate/depth: Read one skip, over the rest
        # We also check that depth is always 4-byte floats (32 bit)
        sampling_rate, depth = cls.decode_rate_depth(read(fp, 'i'))
        skip(fp, nc4 - 4)
        assert depth == 32, f"""
        Unable to read MFF with `depth != 32` [`depth={depth}`]"""
        # Skip the mysterious signal offset 2 (typically 24 bytes)
        padding_byte_size = header_size - 16 - 2 * nc4
        skip(fp, padding_byte_size)
        return cls(
            block_size=block_size,
            header_size=header_size,
            num_samples=num_samples,
            num_channels=num_channels,
            sampling_rate=sampling_rate,
        )

    def to_file(self, fp: FileLike):
        """write HeaderBlock to file pointer `fp`"""
        write(fp, '4i', (
            self.HEADER_PRESENT,
            self.header_size,
            self.block_size,
            self.num_channels
        ))
        num_samples = (self.block_size//self.num_channels) // 4
        # Write channel offset into the data block
        arr = 4 * num_samples * np.arange(self.num_channels).astype(np.int32)
        fp.write(arr.tobytes())
        # write sampling-rate/depth word
        sr_d = self.encode_rate_depth(self.sampling_rate, 32)
        arr = sr_d * np.ones(self.num_channels, dtype=np.int32)
        fp.write(arr.tobytes())
        pad_byte_len = self.header_size - 4 * (4 + 2 * self.num_channels)
        # Pad either with zeros or with the magic `PADDING`
        padding = PADDING if pad_byte_len == len(PADDING) \
            else np.zeros(pad_byte_len, dtype=np.uint8).tobytes()
        fp.write(padding)

    @staticmethod
    def decode_rate_depth(x: int) -> Tuple[int, int]:
        """return rate and depth from encoded representation"""
        rate = x >> 8
        depth = x & 0xff
        return rate, depth

    @staticmethod
    def encode_rate_depth(rate: int, depth: int) -> int:
        """return joined rate and byte depth of samples

        Sampling rate and sample depth are encoded in a single 4-byte integer.
        The first byte is the depth the last 3 bytes give the sampling rate.
        """
        assert depth < (
            1 << 8), f"depth must be smaller than 256 (got {depth})"
        assert rate < (
            1 << 24), f"depth must be smaller than {1<<24} (got {rate})"
        return (rate << 8) + depth

    @staticmethod
    def compute_byte_size(num_channels: int) -> int:
        return 4 * (4 + 2 * num_channels) + len(PADDING)
