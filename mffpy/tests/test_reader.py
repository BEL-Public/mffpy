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
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from .. import Reader

from os.path import join, dirname, isdir
import json


@pytest.fixture
def examples_dir():
    folder = join(dirname(__file__), '..', '..', 'examples')
    assert isdir(folder), f"examples folder not found: '{folder}'"
    return folder


@pytest.fixture
def mffpath(examples_dir):
    """return path to example_1.mff"""
    return join(examples_dir, 'example_1.mff')


@pytest.fixture
def mffpath_2(examples_dir):
    """return path to example_2.mff"""
    return join(examples_dir, 'example_2.mff')


@pytest.fixture
def mffpath_3(examples_dir):
    """return path to example_3.mff"""
    return join(examples_dir, 'example_3.mff')


@pytest.fixture
def mffpath_4(examples_dir):
    """return path to example_4.mff (averaged .mff)"""
    return join(examples_dir, 'example_4.mff')


@pytest.fixture
def signals_3():
    """return signals of example_3.mff extracted with Net Station Tools"""
    csv_file = join(dirname(__file__), '..', 'resources',
                    'testing', 'example_3_signals.csv')
    signals = np.genfromtxt(csv_file, delimiter=',')
    signals = signals.transpose()
    eeg = signals[0:257]
    pns = signals[257:259]
    return eeg, pns


@pytest.fixture
def mfzpath(examples_dir):
    """return path to example_1.mfz"""
    return join(examples_dir, 'example_1.mfz')


@pytest.fixture
def reader(mffpath):
    """return Reader instance from example_1.mff"""
    return Reader(mffpath)


@pytest.fixture
def json_example_2(examples_dir):
    """return content of '/examples/example_2.json'"""
    with open(join(examples_dir, 'example_2.json')) as fp:
        return json.load(fp)


@pytest.mark.parametrize("prop,expected", [
    ('units', {'EEG': 'uV'}),
    ('num_channels', {'EEG': 257}),
    ('startdatetime', datetime(2003, 4, 17, 13, 35, 22,
                               tzinfo=timezone(timedelta(-1, 57600)))),
    ('durations', {'EEG': 16.6}),
    ('sampling_rates', {'EEG': 250.0}),
])
def test_property(prop, expected, reader):
    """test `Reader` reads `prop` of 'example_1.mff'"""
    assert getattr(reader, prop) == expected


@pytest.mark.parametrize("t0,expected_eeg,expected_start", [
    (0.0, [
        48.045338, 49.027397, 55.297466, 46.156765, 34.598686,
        36.336174, 46.61002, 50.689342, 39.811153, 37.24269,
        50.6138, 52.12466, 42.908417, 39.05572, 45.174706,
        50.991516, 41.850815, 39.433437, 48.423054, 48.34751,
        44.570362, 41.01984, 45.32579, 52.65346, 46.76111
    ], 0.0),
    (0.01, [
        55.297466, 46.156765, 34.598686, 36.336174, 46.61002,
        50.689342, 39.811153, 37.24269, 50.6138, 52.12466,
        42.908417, 39.05572, 45.174706, 50.991516, 41.850815,
        39.433437, 48.423054, 48.34751, 44.570362, 41.01984,
        45.32579, 52.65346, 46.76111, 39.73561, 41.926357,
        44.645905
    ], 0.008),
    (0.02, [
        36.336174, 46.61002, 50.689342, 39.811153, 37.24269,
        50.6138, 52.12466, 42.908417, 39.05572, 45.174706,
        50.991516, 41.850815, 39.433437, 48.423054, 48.34751,
        44.570362, 41.01984, 45.32579, 52.65346, 46.76111,
        39.73561, 41.926357, 44.645905, 38.300293, 29.008507
    ], 0.02),
])
def test_get_physical_samples(t0, expected_eeg, expected_start, reader):
    """test `Reader.get_physical_samples_from_epoch`"""
    expected_eeg = np.asarray(expected_eeg, dtype=np.float32)
    data = reader.get_physical_samples_from_epoch(reader.epochs[1], t0, 0.1)
    eeg, start_time = data['EEG']
    eeg = eeg[0]  # select first channel
    assert start_time == expected_start
    # test for equivalence of signal data
    # accurate to the 6th decimal place
    assert eeg == pytest.approx(expected_eeg, abs=1e-6)


def test_get_physical_samples_full_range(reader):
    """test `Reader.get_physical_samples_from_epoch` does not fail"""
    reader.get_physical_samples_from_epoch(reader.epochs[0])


def test_get_physical_samples_multiple_bin_files(signals_3, mffpath_3):
    """Read in signal data from example_3.mff and
    compare to eeg and pns signals extracted
    with Net Station Tools given by test
    fixture signals_3."""
    expected_eeg, expected_pns = signals_3
    mff = Reader(mffpath_3)
    signals = mff.get_physical_samples_from_epoch(mff.epochs[0])
    eeg, eeg_start = signals['EEG']
    pns, pns_start = signals['PNSData']
    assert eeg_start == pns_start == 0.0
    assert eeg == pytest.approx(expected_eeg, abs=1e-6)
    assert pns == pytest.approx(expected_pns, abs=1e-6)


def test_get_mff_content(mffpath_2, json_example_2):
    """test `Reader.get_mff_content` against '/examples/example_2.json'"""
    mff = Reader(mffpath_2)
    mff_content = mff.get_mff_content()
    assert mff_content == json_example_2


def test_startdatetime(mffpath, mfzpath):
    """test equality of .mff and .mfz startdatetime"""
    mff = Reader(mffpath)
    mfz = Reader(mfzpath)
    assert mff.startdatetime == mfz.startdatetime


def test_categories(reader):
    """test querying the categories property through the reader"""
    cats = reader.categories
    assert all(k in cats for k in ('ULRN', 'LRND'))
    assert len(cats['ULRN']) == 50
    assert len(cats['LRND']) == 19


@pytest.mark.parametrize("idx,expected", [
    (0, {'name': 'epoch', 'beginTime': 0, 'endTime': 216000,
         'firstBlock': 1, 'lastBlock': 1}),
    (-2, {'name': 'epoch', 'beginTime': 3323676000, 'endTime': 3359904000,
          'firstBlock': 184, 'lastBlock': 186}),
])
def test_epochs_segmented(reader, idx, expected):
    """test querying the epochs property through
    the reader for a segmented MFF file"""
    read_epoch = reader.epochs[idx]
    for key, exp in expected.items():
        val = getattr(read_epoch, key)
        assert val == exp, f"""
        epochs[{idx}][{key}] = {val} [should be {exp}]"""


def test_index_epochs_by_name_segmented(reader):
    """test indexing epochs by name
    for a segmented MFF file"""
    read_epochs = reader.epochs['epoch']
    assert len(read_epochs) == 53
    for epoch in read_epochs:
        assert epoch.name == 'epoch'


@pytest.mark.parametrize("idx,name,expected", [
    (0, 'Category A', {'name': 'Category A', 'beginTime': 0,
                       'endTime': 20000, 'firstBlock': 1, 'lastBlock': 1}),
    (1, 'Category B', {'name': 'Category B', 'beginTime': 20000,
                       'endTime': 40000, 'firstBlock': 2, 'lastBlock': 2}),
    (2, 'Category C', {'name': 'Category C', 'beginTime': 40000,
                       'endTime': 60000, 'firstBlock': 3, 'lastBlock': 3}),
])
def test_epochs_averaged(mffpath_4, idx, name, expected):
    """test querying the epochs property through
    the reader for an averaged MFF file"""
    mff = Reader(mffpath_4)
    read_epoch = mff.epochs[idx]
    assert read_epoch == mff.epochs[name]
    for key, exp in expected.items():
        val = getattr(read_epoch, key)
        assert val == exp, f"""
        epochs[{idx}][{key}] = {val} [should be {exp}]"""


def test_flavor(mffpath, mffpath_2, mffpath_3, mffpath_4):
    """test `Reader.flavor` for all .mff examples"""
    assert Reader(mffpath).flavor == 'continuous'
    assert Reader(mffpath_2).flavor == 'segmented'
    assert Reader(mffpath_3).flavor == 'continuous'
    assert Reader(mffpath_4).flavor == 'averaged'
