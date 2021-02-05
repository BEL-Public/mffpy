"""Management of header blocks in .mff binary files

.mff binary files have a blocked structure.  Consecutive blocks can be
separated by a header, which brings us to the topic of this module.

The header consists of either a single flag (`flag=0`) or a block describing
the following bytes of signal data (`flag=1`).  Regardless, the flag is 32-bit
wide.

This module adds functionality to read and write these header blocks.

**Header block structure**

+-------------+-------------+---------------------------------------+
| start byte  |  end byte   |              description              |
+-------------+-------------+---------------------------------------+
| 0           | 4           | header flag, if 1, header present     |
| 4           | 8           | bytes in header := `hb`               |
| 8           | 12          | bytes in data blob w/out header       |
| 12          | 16          | channel count := `nc`                 |
| 16          | 16 + 4 * nc | per-channel byte offset               |
| 16 + 4 * nc | 16 + 8 * nc | per-channel frequency and byte depths |
| 16 + 8 * nc | hb          | optional header bytes                 |
+-------------+-------------+---------------------------------------+

Optional header bytes are described in "./optional_header_block.py"
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
    'optional_header'
])


class HeaderBlock(_HeaderBlock):

    def __new__(cls,
                block_size: int,
                num_channels: int,
                num_samples: int,
                sampling_rate: int,
                header_size: Optional[int] = None,
                optional_header: opt.BlockTypes = opt.NoOptHeaderBlock()):
        """create new HeaderBlock instance

        Parameters
        ----------
        block_size : byte size of the block
        num_channels : channel count in the block
        num_samples : sample count per channel in the block
        sampling_rate : sampling_rate per channel in the block
        header_size : byte size of the header (computed if None)
        optional_header : optional header with additional fields
        """
        computed_size = cls.compute_byte_size(num_channels, optional_header)
        if header_size and header_size != computed_size:
            raise ValueError(f"""header of inconsistent size:
            {header_size} != {computed_size}""")

        header_size = computed_size
        return super().__new__(cls, header_size, block_size, num_channels,
                               num_samples, sampling_rate, optional_header)

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
        optional_header = opt.from_file(fp)
        return cls(
            block_size=block_size,
            header_size=header_size,
            num_samples=num_samples,
            num_channels=num_channels,
            sampling_rate=sampling_rate,
            optional_header=optional_header,
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
        self.optional_header.write(fp)

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
    def compute_byte_size(num_channels: int,
                          optional_header: opt.BlockTypes) -> int:
        """returns sum of header byte size and optional header size

        `(5 + ..)`: The 4-byte int of the optional header byte size constitutes
        the "5", not in `optional_header.byte_size`.  See the file description
        for detailed infos on all bytes.
        """
        return 4 * (5 + 2 * num_channels) + optional_header.byte_size
