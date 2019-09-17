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

from ..mffdir import get_directory, MFFDirectory, ZippedMFFDirectory

mff_path = join(dirname(__file__), '..', '..', 'examples', 'example_1.mff')
zipped_mff_path = join(dirname(__file__), '..', '..',
                       'examples', 'example_1.mfz')


@pytest.fixture
def mff():
    """return example_1.mff"""
    d = get_directory(mff_path)
    assert isinstance(d, MFFDirectory)
    return d


@pytest.fixture
def zippedmff():
    """return example_1.mfz"""
    d = get_directory(zipped_mff_path)
    assert isinstance(d, ZippedMFFDirectory)
    return d


def test_listdir(mff, zippedmff):
    """test that listdir finds all content of the .mff file"""
    li = set(mff.listdir())
    zi = set(zippedmff.listdir())
    expected = set(['categories.xml', 'coordinates.xml', 'epochs.xml',
                    'Events_ECI.xml', 'info.xml', 'info1.xml',
                    'sensorLayout.xml', 'signal1.bin', 'subject.xml',
                    'dipoleSet.xml'])
    assert li == expected
    assert li == zi


@pytest.mark.parametrize("asset", ['epochs', 'info'])
def test_read_asset(mff, zippedmff, asset):
    """test that .mff and zipped .mff output the same xml assets"""
    assert mff.filepointer(asset).read() == zippedmff.filepointer(asset).read()


def test_signal_with_info(mff, zippedmff):
    """test `signal_with_info` return the same thing"""
    si = mff.signals_with_info()
    zi = zippedmff.signals_with_info()
    assert len(si) == len(zi)
    si, zi = si[0], zi[0]
    assert si.signal.read() == zi.signal.read()
    info = mff.filepointer(si.info).read()
    znfo = zippedmff.filepointer(zi.info).read()
    assert info == znfo
