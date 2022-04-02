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
from os.path import join, dirname, exists

import pytest
import numpy as np

from ..raw_bin_files import (
    frombuffer, RawBinFile, SEEK_SET, SEEK_CUR, SEEK_END,
)

examples_path = join(dirname(__file__), '..', '..',
                     'examples', 'example_1.mff')


@pytest.fixture
def rawbin():
    ans = join(examples_path, 'signal1.bin')
    assert exists(ans), ans
    return RawBinFile(open(ans, 'rb'))


def test_close(rawbin):
    rawbin.filepointer
    rawbin.close()
    assert rawbin.filepointer.closed


def test_tell(rawbin):
    rawbin.filepointer.seek(10)
    assert rawbin.tell() == 10


def test_seek(rawbin):
    rawbin.seek(10, SEEK_SET)
    assert rawbin.tell() == 10
    rawbin.seek(10, SEEK_CUR)
    assert rawbin.tell() == 20
    rawbin.seek(-10, SEEK_END)
    assert rawbin.tell() == rawbin.bytes_in_file-10


@pytest.mark.parametrize("prop,expected", [
    ('bytes_in_file', 4270376),
    ('num_channels', 257),
    ('sampling_rate', 250.0),
    ('duration', 16.6),
])
def test_property(prop, expected, rawbin):
    assert getattr(rawbin, prop) == expected


@pytest.mark.parametrize("attr,expected", [
    ('num_channels', 257),
    ('sampling_rate', 250.0),
    ('n_blocks', 2),
    ('num_samples', [54, 4096]),
    ('header_sizes', [2100, 2076]),
])
def test_signal_blocks(attr, expected, rawbin):
    val = rawbin.signal_blocks[attr]
    assert val == expected


def test_read_raw_samples(rawbin):
    samples, start_time = rawbin.read_raw_samples(1.0, 1.0)
    vals = samples[:3, :3]
    expected = np.array([
        [-31.280518, -23.498535, -17.77649],
        [-32.348633, -24.94812,  -20.67566],
        [-34.40857,  -25.558472, -20.065308]
    ], dtype=np.float32)
    assert vals == pytest.approx(expected)


def test_read_raw_samples_at_short_intervals(rawbin):
    """check that time interval shorter than sampling rate returns empty"""
    samples, start_time = rawbin.read_raw_samples(0.0, 0.000001)
    assert samples.dtype == np.float32
    assert samples.shape == (257, 0)


def test_frombuffer():
    """tests frombuffer() returns the array"""
    shape = (20, 10)
    expected = np.random.randn(*shape).astype('<f')
    buffer = expected.tobytes()
    array = frombuffer(buffer, shape)
    assert np.all(array == expected)


def test_frombuffer_more_bytes():
    """tests frombuffer() handles one byte too many"""
    shape = (20, 10)
    expected = np.random.randn(*shape).astype('<f')
    buffer = expected.tobytes() + b'\x00'
    with pytest.warns(BytesWarning):
        array = frombuffer(buffer, shape)

    assert np.all(array == expected)


def test_frombuffer_more_floats():
    """tests frombuffer() handles one float (four bytes) too many"""
    shape = (20, 10)
    expected = np.random.randn(*shape).astype('<f')
    buffer = expected.tobytes() + b'\x00' * 4
    with pytest.warns(BytesWarning):
        array = frombuffer(buffer, shape)

    assert np.all(array == expected)


def test_frombuffer_fails():
    """tests frombuffer() raises on invalid shape"""
    shape = (20, 10)
    array = np.random.randn(*shape).astype('<f')
    buffer = array.tobytes()
    with pytest.raises(ValueError):
        frombuffer(buffer, (-1, -1))
