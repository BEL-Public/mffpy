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

from os.path import join, dirname


@pytest.fixture
def mffpath():
    return join(dirname(__file__), '..', '..', 'examples', 'example_1.mff')


@pytest.fixture
def mfzpath():
    return join(dirname(__file__), '..', '..', 'examples', 'example_1.mfz')


@pytest.fixture
def reader(mffpath):
    return Reader(mffpath)


@pytest.mark.parametrize("prop,expected", [
    ('units', {'EEG': 'uV'}),
    ('num_channels', {'EEG': 257}),
    ('startdatetime', datetime(2003, 4, 17, 13, 35, 22,
                               tzinfo=timezone(timedelta(-1, 57600)))),
    ('durations', {'EEG': 16.6}),
    ('sampling_rates', {'EEG': 250.0}),
])
def test_property(prop, expected, reader):
    assert getattr(reader, prop) == expected


@pytest.mark.parametrize("t0,expected_eeg,expected_start", [
    (0.0, [
        48.52295, 49.51477, 55.847168, 46.6156, 34.942627, 36.697388,
        47.073364, 51.193237, 40.20691, 37.612915, 51.116943, 52.642822,
        43.33496, 39.44397, 45.62378, 51.498413, 42.266846, 39.82544, 48.90442,
        48.828125, 45.013428, 41.427612, 45.776367, 53.17688, 47.225952
    ], 0.0),
    (0.01, [
        55.847168, 46.6156, 34.942627, 36.697388, 47.073364, 51.193237,
        40.20691, 37.612915, 51.116943, 52.642822, 43.33496, 39.44397,
        45.62378, 51.498413, 42.266846, 39.82544, 48.90442, 48.828125,
        45.013428, 41.427612, 45.776367, 53.17688, 47.225952, 40.130615,
        42.34314, 45.08972
    ], 0.008),
    (0.02, [
        36.697388, 47.073364, 51.193237, 40.20691, 37.612915, 51.116943,
        52.642822, 43.33496, 39.44397, 45.62378, 51.498413, 42.266846,
        39.82544, 48.90442, 48.828125, 45.013428, 41.427612, 45.776367,
        53.17688, 47.225952, 40.130615, 42.34314, 45.08972, 38.68103,
        29.296875
    ], 0.02),
])
def test_get_physical_samples(t0, expected_eeg, expected_start, reader):
    expected_eeg = np.asarray(expected_eeg, dtype=np.float32)
    data = reader.get_physical_samples_from_epoch(reader.epochs[1], t0, 0.1)
    eeg, start_time = data['EEG']
    eeg = eeg[0]  # select first channel
    assert start_time == expected_start
    assert eeg == pytest.approx(expected_eeg)


def test_get_physical_samples_full_range(reader):
    """read data with default parameters"""
    reader.get_physical_samples_from_epoch(reader.epochs[0])


def test_startdatetime(mffpath, mfzpath):
    mff = Reader(mffpath)
    mfz = Reader(mfzpath)
    assert mff.startdatetime == mfz.startdatetime