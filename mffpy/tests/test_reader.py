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
import json


@pytest.fixture
def mffpath():
    return join(dirname(__file__), '..', '..', 'examples', 'example_1.mff')


@pytest.fixture
def mffpath_2():
    return join(dirname(__file__), '..', '..', 'examples', 'example_2.mff')


@pytest.fixture
def mffpath_3():
    return join(dirname(__file__), '..', '..', 'examples', 'example_3.mff')


@pytest.fixture
def mfzpath():
    return join(dirname(__file__), '..', '..', 'examples', 'example_1.mfz')


@pytest.fixture
def reader(mffpath):
    return Reader(mffpath)


@pytest.fixture
def json_example_2():
    with open(join(dirname(__file__), '..', '..',
                   'examples', 'example_2.json')) as file:
        return json.load(file)


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


@pytest.mark.parametrize("t0,expected_eeg,expected_pns,expected_start", [
    (0.0, [
        -1845.62, -1844.3558, -1844.1255, -1844.5186, -1845.0215, -1844.4167,
        -1843.2725, -1843.3767, -1843.8182, -1844.8408, -1843.2706, -1843.5922
    ], [
        0.21565743, -0.51517457, -1.3356407, -0.16099238, 1.4178662, 0.7046892,
        -0.66320664, -0.09752636, 0.72956467, -0.04039904, -0.14828575,
        1.3500004
    ], 0.0),
    (0.01, [
        -1844.1255, -1844.5186, -1845.0215, -1844.4167, -1843.2725, -1843.3767,
        -1843.8182, -1844.8408, -1843.2706, -1843.5922, -1845.4554, -1844.5149,
        -1843.0234
    ], [
        -1.3356407, -0.16099238, 1.4178662, 0.7046892, -0.66320664,
        -0.09752636, 0.72956467, -0.04039904, -0.14828575, 1.3500004,
        1.0464033, -1.5411711, -1.9540663
    ], 0.008),
    (0.02, [
        -1844.4167, -1843.2725, -1843.3767, -1843.8182, -1844.8408, -1843.2706,
        -1843.5922, -1845.4554, -1844.5149, -1843.0234, -1843.368, -1844.1075,
        -1844.739
    ], [
        0.7046892, -0.66320664, -0.097526364, 0.72956467, -0.040399045,
        -0.14828575, 1.3500004, 1.0464033, -1.5411711, -1.9540663, 0.6091788,
        1.8593298, 1.2873881
    ], 0.02),
])
def test_get_physical_samples_multiple_bins(t0, expected_eeg, expected_pns,
                                            expected_start, mffpath_3):
    expected_eeg = np.asarray(expected_eeg, dtype=np.float32)
    expected_pns = np.asarray(expected_pns, dtype=np.float32)
    mff = Reader(mffpath_3)
    signals = mff.get_physical_samples_from_epoch(mff.epochs[0], t0, 0.05)
    eeg, eeg_start = signals['EEG']
    pns, pns_start = signals['PNSData']
    eeg = eeg[0]
    pns = pns[0]
    assert eeg_start == pns_start == expected_start
    assert eeg == pytest.approx(expected_eeg)
    assert pns == pytest.approx(expected_pns)


def test_get_mff_content(mffpath_2, json_example_2):
    mff = Reader(mffpath_2)
    assert mff.get_mff_content() == json_example_2


def test_startdatetime(mffpath, mfzpath):
    mff = Reader(mffpath)
    mfz = Reader(mfzpath)
    assert mff.startdatetime == mfz.startdatetime
