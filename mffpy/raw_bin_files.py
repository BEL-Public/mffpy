
import struct
from os import SEEK_SET, SEEK_CUR, SEEK_END
from os.path import splitext
import numpy as np
import itertools
from collections import namedtuple
from cached_property import cached_property

from typing import List, Tuple, Dict, Any, IO, Union

DataBlock = namedtuple('DataBlock', 'byte_offset byte_size')
HeaderBlock = namedtuple('HeaderBlock',
        'header_size block_size num_channels num_samples sampling_rate')

class RawBinFile:

    def __init__(self, filepointer: IO[bytes]):
        self.filepointer = filepointer
        assert not self.filepointer.closed
        self.buffering: bool = False

    def __del__(self):
        self.close()

    @cached_property
    def file(self):
        return self.filepointer

    def close(self):
        self.file.close()

    def tell(self) -> int:
        return self.file.tell()

    def seek(self, loc, mode=SEEK_SET):
        assert mode != SEEK_SET or loc>=0
        assert mode != SEEK_END or loc<=0
        return self.file.seek(loc, mode)

    def read(self, format_str: str):
        num_bytes = struct.calcsize(format_str)
        ans = struct.unpack(format_str, self.file.read(num_bytes))
        return ans if len(ans)>1 else ans[0]

    @cached_property
    def bytes_in_file(self):
        loc = self.tell()
        self.seek(0, mode=SEEK_END)
        bytes_in_file = self.tell()
        self.seek(loc, mode=SEEK_SET)
        return bytes_in_file
    
    @property
    def num_channels(self) -> int:
        return self.signal_blocks['num_channels']
    
    @property
    def sampling_rate(self) -> float:
        return self.signal_blocks['sampling_rate']

    @property
    def num_samples(self) -> int:
        """returns number of samples per channel in file"""
        return self.block_start_idx[-1]

    @property
    def duration(self) -> float:
        """returns duration of file in seconds"""
        return self.num_samples / self.sampling_rate

    @cached_property
    def signal_blocks(self) -> Dict[str, Union[int, float, list]]:
        """return dictionary describing the signal file

        This cached property reads through all headers in the blocked binary
        structure.  Each block can have a varying number of samples.
        """
        num_samples, num_channels, header_sizes, sampling_rate, data \
                = [], [], [], [], []
        hdr: Union[HeaderBlock, None] = None
        self.seek(0)
        for block_idx in itertools.count():
            if self.tell() >= self.bytes_in_file:
                break
            # Each block starts with a byte-long header flag which is
            # * `0`: there is no header
            # * `1`: it follows a header
            if self.read('i'):
                hdr = self._read_header_block()
                # we only need to read this here b/c we are not
                # using `sampling_rate` of all the different headers.
                # (We assume they are equal)
                sampling_rate.append(hdr.sampling_rate)
                num_channels.append(hdr.num_channels)
            else:
                assert hdr is not None, f"First block must be a header"
                # hdr is the hdr of the previous block: `num_samples` did not
                # change.

            data.append(DataBlock(self.tell(), hdr.block_size))
            num_samples.append(hdr.num_samples)
            header_sizes.append(hdr.header_size)
            self._skip_over(hdr.block_size)

        # Check that ..
        #   * number of channels does not change across blocks
        #   * sampling rates do not change across blocks
        #   * there are samples present
        assert hdr is not None
        assert all(n == num_channels[0] for n in num_channels), "Found different channel number while reading header blocks"
        assert all(sr == sampling_rate[0] for sr in sampling_rate), "Found different sampling rates while reading blocks"
        assert len(num_samples) > 0, f"No data found [`num_samples={num_samples}`]"

        return {
            'data': data,
            'n_blocks': block_idx,
            'num_samples': num_samples,
            'num_channels': num_channels[0],
            'header_sizes': header_sizes,
            'sampling_rate': sampling_rate[0]
        }

    def _read_header_block(self) -> HeaderBlock:
        """return a header block read at the current file pointer

        **Header block content**
        byte 0 : header flag (already read; fp is at position 1)
        byte 1 : number of bytes in the header
        byte 2 : number of bytes in the following data block
        byte 3 : number of channels in the data block
        bytes 4 to 4+nc : byte offset in the block for each signal
            (we skip this)
        bytes 4+nc to 4+nc*2 : signal frequencies,word 1,
            and depths, word 2, (we read one and skip over the rest)

        **Returns**
        A BlockHeader tuple

        (sr_d: combined sampling frequencies and depths)
        """
        # Read general information
        header_size, block_size, num_channels = self.read('3i')
        # number of 4-byte samples per channel in the data block
        num_samples = (block_size//num_channels) // 4
        # Read channel-specific information
        nc4 = 4 * num_channels
        # Skip byte offsets
        self._skip_over(nc4)
        # Sample rate/depth: Read one skip, over the rest
        # We also check that depth is always 4-byte floats (32 bit)
        sr_d = self.read('i')
        self._skip_over(nc4-4)
        depth = sr_d & 0xFF
        sampling_rate = sr_d >> 8
        assert depth == 32, f"Unable to read MFF with `depth != 32` [`depth={depth}`]"
        # Skip the mysterious signal offset 2 (typically 24 bytes)
        count = header_size - 4 * 4 - 2 * nc4
        self._skip_over(count)
        return HeaderBlock(
            block_size = block_size,
            header_size = header_size,
            num_samples = num_samples,
            num_channels = num_channels,
            sampling_rate = sampling_rate,
        )

    def _skip_over(self, block_size: int):
        """Skip filepointer over `block_size` bytes"""
        self.seek(block_size, mode=SEEK_CUR)

    @cached_property
    def block_start_idx(self) -> np.ndarray:
        return np.cumsum(
            [0]+self.signal_blocks['num_samples'])

    def _read_blocks(self, A: int, B: int, num_channels: int) -> np.ndarray:

        def read_block(block):
            self.seek(block.byte_offset)
            buf = self.file.read(block.byte_size)
            data = np.frombuffer(buf, '<f4', count=-1)
            return data.reshape(num_channels, -1, order='C')

        return np.concatenate([
            read_block(self.signal_blocks['data'][i])
            for i in range(A, B)
        ], axis=1)

    def read_raw_samples(self, t0: float = 0.0, dt: float = None,
            block_slice: slice = None) -> Tuple[np.ndarray, float]:
        """return `(channels, samples)`-array and `start_time` of data

        The signal data is organized in variable-sized blocks that enclose
        epochs of continuous recordings.  Discontinuous breaks can happen in
        between blocks.  `block_slice` indexes into such epochs if not None,
        but we might want only a small chunk of it given by `t0` and `dt`.
        Therefore, we further index into blocks `bsi` selected through
        block_slice with the variables `A` and `B`.  Block indices `A` and `B`
        are chosen to enclose the interval `(t0, t0+dt)` which we would like to
        read.

        **Parameters**
        t0: float (default: 0.0)
            Start time to read out data, starting at the beginning of the block.
        dt: float (default: None)
            duration of the data to read out.  `None` defaults to the rest of
            the signal.
        block_slice: slice (default: None)
            blocks to consider when reading data.

        **Returns**
        block_data: np.ndarray
            array containing all samples between the samples enclosing
            `(t0,t0+dt)` relative to the block slice.
        time_of_first_sample: float
            time in seconds from file start of the first returned sample.
        """
        assert block_slice is None or isinstance(block_slice, slice)
        block_slice = block_slice if block_slice else slice(0, len(self.block_start_idx)-1)
        # Calculate .. the relative sample index of `t0` and `t0+dt`
        # with respect to the beginning of the epoch (block_slice)
        sr = self.signal_blocks['sampling_rate']
        a = np.round(t0*sr).astype(int) if t0 is not None else None
        b = np.round((t0+dt)*sr).astype(int) if dt is not None else None
        time_of_first_sample = a/sr
        # .. the (relative) block index enclosing `bsi[0]+a` and `bsi[0]+b`
        bsi = self.block_start_idx[block_slice]
        A = bsi.searchsorted(bsi[0]+a, side='right')-1 if a is not None  else 0
        B = bsi.searchsorted(bsi[0]+b, side='left') if b is not None else len(bsi)
        # .. the relative sample size index with respect to the blocks that
        # indices (A,B) determine.
        if a is not None:
            a -= bsi[A]-bsi[0]
        if b is not None:
            b -= bsi[A]-bsi[0]
        # .. the (absolute) block index enclosing <..>
        A += block_slice.start
        B += block_slice.start
        # access the file to read the data
        block_data = self._read_blocks(A, B, self.signal_blocks['num_channels'])
        # reject offsets (a,b) that go beyond blocks
        block_data = block_data[:, a:b]
        return block_data, time_of_first_sample
