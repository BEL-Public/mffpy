
import pytest
import numpy as np
from .raw_bin_files import RawBinFile, SEEK_END, SEEK_BEGIN, SEEK_RELATIVE

from os.path import join, dirname, exists

PATH = join(dirname(__file__), '..', 'examples', 'example_1.mff')

@pytest.fixture
def rawbin():
    ans = join(PATH, 'signal1.bin')
    assert exists(ans), ans
    return RawBinFile(ans)

def test_close(rawbin):
    f = rawbin.file
    rawbin.close()
    assert rawbin.file.closed

def test_tell(rawbin):
    rawbin.file.seek(10)
    assert rawbin.tell() == 10

def test_seek(rawbin):
    rawbin.seek(10, SEEK_BEGIN)
    assert rawbin.tell() == 10
    rawbin.seek(10, SEEK_RELATIVE)
    assert rawbin.tell() == 20
    rawbin.seek(-10, SEEK_END)
    assert rawbin.tell() == rawbin.bytes_in_file-10

def test_read(rawbin):
    r = rawbin.read('4i')
    assert all(ri == exp for ri, exp in zip(r,[1, 2100, 55512, 257]))

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
   ('num_samples_by_block', [54, 4096]),
   ('header_sizes', [2100, 2076]),
])
def test_signal_blocks(attr, expected, rawbin):
    val = rawbin.signal_blocks[attr]
    if isinstance(val, list):
        assert val == pytest.approx(expected)
    else:
        assert val == expected

def test_read_raw_samples(rawbin):
    samples, start_time = rawbin.read_raw_samples(1.0, 1.0)
    vals = samples[:3,:3]
    expected = np.array([
        [-31.280518, -23.498535, -17.77649 ],
        [-32.348633, -24.94812,  -20.67566 ],
        [-34.40857,  -25.558472, -20.065308]
    ], dtype=np.float32)
    assert vals == pytest.approx(expected)
