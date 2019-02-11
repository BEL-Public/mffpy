
import struct
from os.path import splitext
import numpy as np
import itertools
from collections import namedtuple
from cached_property import cached_property

from typing import List, Tuple, Dict, Any

SEEK_BEGIN = 0
SEEK_RELATIVE = 1
SEEK_END = 2

DataBlock = namedtuple('DataBlock', 'byte_offset byte_size')

class RawBinFile:

    _extensions: Tuple[str] = ('.bin',)
    _ext_err: str = "Unknown file type [extension has to be one of %s]"
    _supported_versions: Tuple[str] = ('',)
    _flag_format: str = 'i'

    def __init__(self, filename: str):
        self.filename = filename
        self._check_ext()
        self.buffering: bool = False

    def _check_ext(self):
        assert splitext(self.filename)[1] in self._extensions, self._ext_err%self._extensions

    def __del__(self):
        self.close()

    @cached_property
    def file(self):
        return open(self.filename, 'rb', buffering=self.buffering)

    def close(self):
        self.file.close()

    def tell(self) -> int:
        return self.file.tell()

    def seek(self, loc, mode=SEEK_BEGIN):
        assert mode!=SEEK_BEGIN or loc>=0
        assert mode!=SEEK_END or loc<=0
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
        self.seek(loc, mode=SEEK_BEGIN)
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
    def signal_blocks(self) -> Dict[str, Any]:
        num_samples_by_block, num_channels = [], []
        header_sizes, sampling_rate = [], []
        self.data_blocks: List[DataBlock] = []
        header = None
        self.seek(0)
        for block_idx in itertools.count():
            if self.tell() >= self.bytes_in_file:
                break
            if self.next_block_starts_with_header():
                header = self._read_header_block()
                header_sizes.append(header['header_size'])
                num_samples_by_block.append(header['num_samples'])
                sampling_rate.append(header['sampling_rate'])
                num_channels.append(header['num_channels'])
            else:
                assert header is not None, "First block must be a header.  Header flag was: %s"%self._current_header_flag
                num_samples_by_block.append(header['num_samples'])

            self.data_blocks.append(DataBlock(self.tell(), header['block_size']))
            self._skip_data_block(header['block_size'])

        assert all(n == num_channels[0] for n in num_channels), "Blocks don't have the same amount of channels."
        assert all(sr == sampling_rate[0] for sr in sampling_rate), "All the blocks don't have the same sampling frequency."
        assert len(num_samples_by_block) > 0, "No data found [`num_samples_by_block=%s`]"%num_samples_by_block

        num_samples_by_block = num_samples_by_block
        return dict(
            num_channels = num_channels[0],
            sampling_rate = sampling_rate[0],
            n_blocks = block_idx,
            num_samples_by_block = num_samples_by_block,
            header_sizes = header_sizes
        )

    def next_block_starts_with_header(self) -> bool:
        """returns `True` if next block starts with a header.
        
        Each block starts with a 4-byte integer flag:  the block has an
        additional header pre-appended if the flag equals `1`, else it's
        only a data block.
        """
        self._current_header_flag = self.read(self._flag_format)
        return self._current_header_flag == 1

    def _read_header_block(self) -> Dict[str, Any]:
        """returns a header block read from the current file pointer position.

        To Do:
        * What is `sigoffset` and `sigoffset2`?  How is it used?
        """
        keys = ('header_size', 'block_size', 'num_channels')
        # prior we already read 1 * 4 bytes (flag)
        # read 3 * 4 bytes (4 * 4bytes):
        header = dict(zip(keys, self.read('3i')))
        # number of 4-byte samples in the data block
        hl = header['block_size']//4
        # number of channels in the data block
        nc = header['num_channels']
        # number of samples per channel in the data block
        num_samples = hl//nc
        channel_fmt = str(header['num_channels'])+'i'
        # read nc * 4bytes ((4+nc) * 4bytes):
        sigoffset = self.read(channel_fmt) # read 1 * nc * 4 bytes
        # read nc * 4bytes ((4+2*nc) * 4bytes):
        sigfreq = self.read(channel_fmt) # read 1 * nc * 4 bytes
        depth = sigfreq[0] & 0xFF
        assert depth == 32, 'Unable to read MFF with `depth != 32` [`depth=%s`]'%depth
        sampling_rate = sigfreq[0] >> 8
        count = int(header['header_size'] / 4 - (4 + 2 * nc))
        # optional header byte length (typically 24 bytes):
        sigoffset2 = self.read(str(count)+'i')
        header['hl'] = hl
        # number of samples per channel in the data block
        header['num_samples'] = num_samples
        header['sampling_rate'] = sampling_rate
        return header

    def _skip_data_block(self, block_size: int):
        self.seek(block_size, mode=SEEK_RELATIVE)

    @cached_property
    def block_start_idx(self) -> np.ndarray:
        return np.cumsum(
            [0]+self.signal_blocks['num_samples_by_block'])

    def _read_blocks(self, A: int, B: int, num_channels: int) -> np.ndarray:

        def read_block(block):
            self.seek(block.byte_offset)
            buf = self.file.read(block.byte_size)
            data = np.frombuffer(buf, '<f4', count=-1)
            return data.reshape(num_channels, -1, order='C')

        return np.concatenate([
            read_block(self.data_blocks[i])
            for i in range(A, B)
        ], axis=1)

    def read_raw_samples(self, t0: float=0.0, dt: float=None, block_slice: slice=None) -> Tuple[np.ndarray, float]:
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
        a -= bsi[A]-bsi[0]
        b -= bsi[A]-bsi[0]
        # .. the (absolute) block index enclosing <..>
        A += block_slice.start
        B += block_slice.start
        # access the file to read the data
        block_data = self._read_blocks(A, B, self.signal_blocks['num_channels'])
        # reject offsets (a,b) that go beyond blocks
        block_data = block_data[:, a:b]
        return block_data, time_of_first_sample
