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

from ..zipfile import ZipFile
from zipfile import ZipFile as stlZipFile

examples_path = join(dirname(__file__), '..', '..', 'examples')


@pytest.fixture
def stlmff():
    """load zipped mff file with standard `zipfile`"""
    filename = join(examples_path, 'example_1.mfz')
    return stlZipFile(filename)


@pytest.fixture
def mymff():
    """load zipped mff file with custom `zipfile`"""
    filename = join(examples_path, 'example_1.mfz')
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
