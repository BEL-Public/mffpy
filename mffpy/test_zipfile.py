
from os.path import join, dirname

import pytest

from .zipfile import ZipFile
from zipfile import ZipFile as stlZipFile

examples_path = join(dirname(__file__), '..', 'examples')

@pytest.fixture
def stlmff():
    """load zipped mff file with standard `zipfile`"""
    filename = join(examples_path, 'zipped_example_1.mff')
    return stlZipFile(filename)

@pytest.fixture
def mymff():
    """load zipped mff file with custom `zipfile`"""
    filename = join(examples_path, 'zipped_example_1.mff')
    return ZipFile(filename)

def test_enter(mymff, stlmff):
    """test enter and read from a `FilePart`"""
    expected = stlmff.open("epochs.xml").read()
    with mymff.open('epochs.xml') as fp:
        output = fp.read()
    assert fp.closed
    assert output == expected

def test_close(mymff):
    """test closing a `FilePart`"""
    fp = mymff.open('epochs.xml')
    fp.close()
    assert fp.closed

def test_seek_tell(mymff):
    """test seek in a `FilePart`"""
    with mymff.open('epochs.xml') as fp:
        assert fp.tell() == 0
        fp.seek(12)
        assert fp.tell() == 12
        fp.seek(12, 1)
        assert fp.tell() == 2*12
        fp.seek(0, 2)
        assert fp.tell() == fp.end-fp.start

@pytest.mark.parametrize('whence', [-1, 3])
def test_wrong_whence(mymff, whence):
    """test wrong `whence` parameter throws `ValueError`"""
    with mymff.open('epochs.xml') as fp:
        with pytest.raises(ValueError):
            fp.seek(0, whence)
