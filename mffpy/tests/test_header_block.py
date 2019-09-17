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
from os.path import join, dirname
import pytest
from ..header_block import (
    HeaderBlock,
    read_header_block,
    write_header_block
)

from io import BytesIO


@pytest.fixture
def dummy_header():
    sampling_rate = 256
    num_samples = 128
    num_channels = 64
    block_size = 4 * num_samples * num_channels
    nc4 = 4 * num_channels
    header_size = 4 * 4 + 2 * nc4 + 33
    return HeaderBlock(
        block_size=block_size,
        header_size=header_size,
        num_samples=num_samples,
        num_channels=num_channels,
        sampling_rate=sampling_rate
    )


@pytest.fixture
def example_header_bytes():
    example_bin_file = join(dirname(__file__), '..', '..',
                            'examples', 'example_1.mff', 'signal1.bin')
    with open(example_bin_file, 'rb') as fp:
        header = read_header_block(fp)
        fp.seek(0)
        byts = fp.read(header.header_size)
    return header, byts


def test_written_header(example_header_bytes, dummy_header):
    example_header, _ = example_header_bytes
    fp = BytesIO()
    # write the header two times
    write_header_block(fp, example_header)
    write_header_block(fp, dummy_header)
    # read into `HeaderBlock` objects and compare
    fp.seek(0)
    assert example_header == read_header_block(fp)
    assert dummy_header == read_header_block(fp)


def test_written_header_bytes(example_header_bytes):
    header, byts = example_header_bytes
    print(header)
    print(len(byts))
    fp = BytesIO()
    write_header_block(fp, header)
    fp.seek(0)
    output_byts = fp.read()
    assert len(output_byts) == len(byts)
    assert output_byts == byts
