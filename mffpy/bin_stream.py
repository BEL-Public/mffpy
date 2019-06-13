
from os import SEEK_SET
from io import BytesIO
from typing import List, Union

import numpy as np

from .epoch import Epoch
from .header_block import *

class BinStream:

    def __init__(self, sampling_rate: int):
        """
        **Note**

        Sampling rate has to be 3-byte integer 
        """
        self.sampling_rate = sampling_rate
        self.header: Union[HeaderBlock, None] = None
        self.stream = BytesIO()
        self.epochs: List[Epoch] = []

    def add_block_to_epochs(self, num_samples, offset_us=0):
        duration_us = int(10**6 * num_samples * self.sampling_rate)
        if len(self.epochs) == 0:
            # add a first epoch
            self.epochs.append(Epoch(
                beginTime = offset_us,
                endTime = offset_us + duration_us,
                firstBlock = 1,
                lastBlock = 1
            ))
        elif offset_us > 0:
            # create a new epoch
            beginTime = self.epochs[-1].endTime + offset_us
            blockIdx = self.epochs[-1].lastBlock + 1
            self.epochs.append(Epoch(
                beginTime = beginTime,
                endTime = beginTime + duration_us,
                firstBlock = blockIdx,
                lastBlock = blockIdx
            ))
        else:
            # add block to current epoch
            self.epochs[-1].add_block(duration_us)

    def add_block(self, data: np.ndarray, offset_us: int = 0):
        num_channels, num_samples = data.shape
        assert data.dtype == np.float32
        # Check if the header needs to be modified
        if self.header is None:
            self.header = HeaderBlock(
                block_size = 4 * data.size,
                header_size = compute_header_byte_size(num_channels),
                num_samples = num_samples,
                num_channels = num_channels,
                sampling_rate = self.sampling_rate,
            )
        else:
            assert num_channels == self.header.num_channels
            self.header = HeaderBlock(
                block_size = 4 * data.size,
                header_size = self.header.header_size,
                num_samples = num_samples,
                num_channels = num_channels,
                sampling_rate = self.sampling_rate,
            )
        # Write header/data to stream, and add an epochs block
        write_header_block(self.stream, self.header)
        self.append(data.tobytes())
        self.add_block_to_epochs(num_samples, offset_us=offset_us)

    def seek(self, loc: int, mode: int = SEEK_SET) -> int:
        return self.stream.seek(loc, mode)

    def append(self, b: bytes):
        num_written = self.stream.write(b)
        assert num_written == len(b)

    def write(self, filename: str, *args, **kwargs):
        # *args, **kwargs are ignored
        self.seek(0)
        byts = self.stream.read()
        with open(filename, 'wb') as fo:
            num_written = fo.write(byts)
        assert num_written == len(byts)
