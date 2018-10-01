
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

    def __init__(self, filename):
        self.filename = filename
        self._check_ext()
        self.buffering = False

    def _check_ext(self):
        assert splitext(self.filename)[1] in self._extensions, self._ext_err%self._extensions

    def __del__(self):
        self.close()

    @property
    def file(self):
        try:
            return self._file
        except AttributeError:
            self._file = open(self.filename, 'rb', buffering=self.buffering)
        return self.file

    def close(self):
        if hasattr(self, '_file'):
            self._file.close()

    def tell(self):
        return self.file.tell()

    def seek(self, loc, mode=SEEK_BEGIN):
        return self.file.seek(loc, mode)

    def read(self, format_str):
        num_bytes = struct.calcsize(format_str)
        ans = struct.unpack(format_str, self.file.read(num_bytes))
        return ans if len(ans)>1 else ans[0]

    @property
    def bytes_in_file(self):
        try:
            return self._bytes_in_file
        except AttributeError:
            loc = self.tell()
            self.seek(0, mode=SEEK_END)
            self._bytes_in_file = self.tell()
            self.seek(loc, mode=SEEK_BEGIN)
        return self.bytes_in_file

    def next_block_starts_with_header(self):
        """returns `True` if next block starts with a header.
        
        Each block starts with a 4-byte integer flag:  the block has an
        additional header pre-appended if the flag equals `1`, else it's
        only a data block.
        """
        return self.read(self._flag_format) == 1

    def _read_header_block(self):
        keys = ('header_size', 'block_size', 'num_channels')
        header = dict(zip(keys, self.read('3i')))
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
        self.seek(block_size, mode=SEEK_RELATIVE)

    def read_meta_info(self):
        num_samples_by_block, num_channels = [], []
        header_sizes, sampling_rate = [], []
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
                assert header is not None, "First block must be a header."
                num_samples_by_block.append(header['num_samples'])

            self._skip_data_block(header['block_size'])

        assert all(n == num_channels[0] for n in num_channels), "Blocks don't have the same amount of channels."
        assert all(sr == sampling_rate[0] for sr in sampling_rate), "All the blocks don't have the same sampling frequency."
        assert len(num_samples_by_block) > 0, "No data found [`num_samples_by_block=%s`]"%num_samples_by_block
        
        num_samples_by_block = np.array(num_samples_by_block)
        self.signal_blocks = dict(
            num_channels = num_channels[0],
            sampling_rate = sampling_rate[0],
            n_blocks = block_idx,
            num_samples_by_block = num_samples_by_block,
            header_sizes = header_sizes
        )
