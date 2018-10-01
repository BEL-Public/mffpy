
import struct
from os.path import join, splitext
import contextlib
import numpy as np
import itertools

SEEK_BEGIN = 0
SEEK_RELATIVE = 1
SEEK_END = 2

class BinFile:

    _extensions = ('.bin',)
    _ext_err = "Unknown file type [extension has to be one of %s]"
    _supported_versions = (None,)
    _flag_format = 'i'

    def __init__(self, filename, keep_open=True):
        self.filename = filename
        self.keep_open = keep_open
        self._check_ext()
        self._file = open(filename, 'rb') if keep_open else None
        self.current_file_location = 0

    def _check_ext(self):
        assert splitext(self.filename)[1] in self._extensions, self._ext_err%self._extensions

    def __del__(self):
        if self.keep_open:
            self.close()

    def open(self):
        if not self.keep_open:
            self._file = open(self.filename, 'rb')
        return self._file

    def close(self):
        self._file.close()

    @contextlib.contextmanager
    def file(self):
        if self.keep_open:
            yield self._file
        else:
            self._file = open(self.filename, 'rb')
            self._file.seek(self.current_file_location)
            try:
                yield self._file
            finally:
                self.current_file_location = self._file.tell()
                self._file.close()
                self._file = None

    def tell(self):
        with self.file() as f:
            return f.tell()

    def seek(self, loc, mode=SEEK_BEGIN):
        if loc == self.current_file_location:
            return None
        with self.file() as f:
            f.seek(loc, mode)
            self.current_file_location = f.tell()

    def read(self, format_str):
        num_bytes = struct.calcsize(format_str)
        with self.file() as f:
            ans = struct.unpack(format_str, f.read(num_bytes))
        return ans if len(ans)>1 else ans[0]

    def peek(self, format_str):
        with self.file() as f:
            # self.tell()
            loc = f.tell()
            # self.read(format_str)
            num_bytes = struct.calcsize(format_str)
            ans = struct.unpack(format_str, f.read(num_bytes))
            ans = ans if len(ans)>1 else ans[0]
            # self.seek(loc)
            f.seek(loc)
        return ans

    @property
    def bytes_in_file(self):
        try:
            return self._bytes_in_file
        except AttributeError:
            with self.file() as f:
                f.seek(0, SEEK_END)
                self._bytes_in_file = f.tell()
                f.seek(self.current_file_location)
        return self.bytes_in_file

    def next_block_starts_with_header(self):
        """returns `True` if next block starts with a header.
        
        Each block starts with a 4-byte integer flag:  the block has an
        additional header pre-appended if the flag equals `1`, else it's
        only a data block.
        """
        return self.peek(self._flag_format) == 1

    def _read_header_block(self):
        keys = ('flag', 'header_size', 'block_size', 'num_channels')
        header = dict(zip(keys, self.read('4i')))
        hl = header['block_size']//4
        nc = header['num_channels']
        channel_fmt = str(header['num_channels'])+'i'
        sigoffset = self.read(channel_fmt)
        sigfreq = self.read(channel_fmt)
        depth = sigfreq[0] & 0xFF
        assert depth == 32, 'Unable to read MFF with `depth != 32` [`depth=%s`]'%depth
        sampling_rate = sigfreq[0] >> 8
        count = int(header['header_size'] / 4 - (4 + 2 * nc))
        sigoffset2 = self.read(str(count)+'i')
        header['hl'] = hl
        header['num_samples'] = hl//nc
        header['sampling_rate'] = sampling_rate
        return header

    def _skip_data_block(self, block_size):
        # flag_byte_size = struct.calcsize(self._flag_format)
        flag_byte_size = 4
        self.seek(block_size+flag_byte_size, mode=SEEK_RELATIVE)

    def read_meta_info(self):
        block_idx = 0
        num_samples_by_block, num_channels = [], []
        header_sizes, sampling_rate = [], []
        header = None
        self.seek(0)
        for block_idx in itertools.count():
            if self.current_file_location >= self.bytes_in_file:
                num_blocks = block_idx
                break
            if self.next_block_starts_with_header():
                header = self._read_header_block()
                header_sizes.append(header['header_size'])
                num_samples_by_block.append(header['num_samples'])
                sampling_rate.append(header['sampling_rate'])
                num_channels.append(header['num_channels'])
                self.seek(header['block_size'], mode=SEEK_RELATIVE)
            else:
                assert header is not None, "First block must be a header."
                num_samples_by_block.append(header['num_samples'])
                self._skip_data_block(header['block_size'])

        assert all(n == num_channels[0] for n in num_channels), "Blocks don't have the same amount of channels."
        assert all(sr == sampling_rate[0] for sr in sampling_rate), "All the blocks don't have the same sampling frequency."
        assert len(num_samples_by_block) > 0, "No data found"
        
        num_samples_by_block = np.array(num_samples_by_block)
        self.signal_blocks = dict(
            num_channels = num_channels[0],
            sampling_rate = sampling_rate[0],
            n_blocks = num_blocks,
            num_samples_by_block = num_samples_by_block,
            header_sizes = header_sizes
        )
