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
from typing import Optional, Tuple
from collections import namedtuple

import numpy as np

from .helpers import FileLike, read, skip, write
from . import optional_header_block as opt

HEADER_BLOCK_PRESENT = 1

_HeaderBlock = namedtuple('_HeaderBlock', [
    'header_size',
    'block_size',
    'num_channels',
    'num_samples',
    'sampling_rate',
    'optional'
])


class HeaderBlock(_HeaderBlock):

    def __new__(cls,
                block_size: int,
                num_channels: int,
                num_samples: int,
                sampling_rate: int,
                header_size: Optional[int] = None,
                optional: opt.BlockTypes = opt.NoOptHeaderBlock()):
        """create new HeaderBlock instance

        Parameters
        ----------
        block_size : byte size of the block
        num_channels : channel count in the block
        num_samples : sample count per channel in the block
        sampling_rate : sampling_rate per channel in the block
        header_size : byte size of the header (computed if None)
        optional : tuple containing optional header fields
        """
        if header_size:
            computed_header_size = cls.compute_byte_size(
                num_channels, optional)
            assert header_size == computed_header_size, f"""
            inconsistent header {header_size} != {computed_header_size}"""
        else:
            header_size = cls.compute_byte_size(num_channels, optional)

        return super().__new__(cls, header_size, block_size, num_channels,
                               num_samples, sampling_rate, optional)

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
        # Skip byte offsets
        skip(fp, 4 * num_channels)
        # Sample rate/depth: Read one skip, over the rest
        # We also check that depth is always 4-byte floats (32 bit)
        sampling_rate, depth = cls.decode_rate_depth(read(fp, 'i'))
        skip(fp, 4 * (num_channels - 1))
        assert depth == 32, f"""
        Unable to read MFF with `depth != 32` [`depth={depth}`]"""
        optional = opt.from_file(fp)
        return cls(
            block_size=block_size,
            header_size=header_size,
            num_samples=num_samples,
            num_channels=num_channels,
            sampling_rate=sampling_rate,
            optional=optional,
        )

    def write(self, fp: FileLike):
        """write HeaderBlock to file pointer `fp`"""
        write(fp, '4i', (
            HEADER_BLOCK_PRESENT,
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
        self.optional.write(fp)

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
    def compute_byte_size(num_channels: int, optional) -> int:
        return 4 * (5 + 2 * num_channels) + optional.byte_size
