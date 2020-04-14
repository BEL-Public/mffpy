"""
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
"""

import struct
from os import SEEK_CUR
from typing import IO, Union
from collections import namedtuple
from io import FileIO

import numpy as np

__all__ = [
    'HeaderBlock',
    'read_header_block',
    'write_header_block',
    'compute_header_byte_size'
]

HeaderBlock = namedtuple('HeaderBlock', [
    'header_size',
    'block_size',
    'num_channels',
    'num_samples',
    'sampling_rate'
])


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


def encode_rate_depth(rate: int, depth: int):
    """return joined rate and byte depth of samples

    Sampling rate and sample depth are encoded in a single 4-byte integer.  The
    first byte is the depth the last 3 bytes give the sampling rate.
    """
    assert depth < (1 << 8), f"depth must be smaller than 256 (got {depth})"
    assert rate < (1 << 24), f"depth must be smaller than {1<<24} (got {rate})"
    return (rate << 8) + depth


def decode_rate_depth(x: int):
    """return rate and depth from encoded representation"""
    rate = x >> 8
    depth = x & 0xff
    return rate, depth


def compute_header_byte_size(num_channels):
    return 4 * (4 + 2 * num_channels) + len(PADDING)


def read_header_block(filepointer: IO[bytes]):
    """return HeaderBlock, read from fp"""

    def read(format_str: str):
        num_bytes = struct.calcsize(format_str)
        byts = filepointer.read(num_bytes)
        ans = struct.unpack(format_str, byts)
        return ans if len(ans) > 1 else ans[0]

    def skip(n: int):
        filepointer.seek(n, SEEK_CUR)

    # Each block starts with a 4-byte-long header flag which is
    # * `0`: there is no header
    # * `1`: it follows a header
    if read('i') == 0:
        return None
    # Read general information
    header_size, block_size, num_channels = read('3i')
    # number of 4-byte samples per channel in the data block
    num_samples = (block_size//num_channels) // 4
    # Read channel-specific information
    nc4 = 4 * num_channels
    # Skip byte offsets
    skip(nc4)
    # Sample rate/depth: Read one skip, over the rest
    # We also check that depth is always 4-byte floats (32 bit)
    sampling_rate, depth = decode_rate_depth(read('i'))
    skip(nc4-4)
    assert depth == 32, f"""
    Unable to read MFF with `depth != 32` [`depth={depth}`]"""
    # Skip the mysterious signal offset 2 (typically 24 bytes)
    padding_byte_size = header_size - 16 - 2 * nc4
    skip(padding_byte_size)
    return HeaderBlock(
        block_size=block_size,
        header_size=header_size,
        num_samples=num_samples,
        num_channels=num_channels,
        sampling_rate=sampling_rate,
    )


def write_header_block(fp: Union[IO[bytes], FileIO], hdr: HeaderBlock):
    """write HeaderBlock `hdr` to file pointer `fp`"""
    fp.write(struct.pack('4i',
                         1, hdr.header_size, hdr.block_size, hdr.num_channels))
    num_samples = (hdr.block_size//hdr.num_channels) // 4
    # Write channel offset into the data block
    arr = 4 * num_samples * np.arange(hdr.num_channels).astype(np.int32)
    fp.write(arr.tobytes())
    # write sampling-rate/depth word
    sr_d = encode_rate_depth(hdr.sampling_rate, 32)
    arr = sr_d * np.ones(hdr.num_channels, dtype=np.int32)
    fp.write(arr.tobytes())
    pad_byte_len = hdr.header_size - 4 * (4 + 2 * hdr.num_channels)
    # Pad either with zeros or with the magic `PADDING`
    padding = PADDING if pad_byte_len == len(PADDING) \
        else np.zeros(pad_byte_len, dtype=np.uint8).tobytes()
    fp.write(padding)
