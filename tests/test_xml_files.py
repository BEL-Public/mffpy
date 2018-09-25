
# B/c the module is not compiled we can import the current version
from sys import path
from os.path import join, exists, dirname
path.insert(0, join(dirname(__file__),'..'))

import pytest
import numpy as np
from mffpy.io.egi.xml_files import (
    FileInfo, DataInfo,
    Patient, SensorLayout,
    Coordinates, Epochs,
    EventTrack
)
from datetime import datetime

PATH = join(dirname(__file__), '..', 'examples', 'example_1.mff')

"""
Here are several fixtures that parse example xml files
to be tested.  The files parsed are located in `PATH`.
"""

@pytest.fixture
def file_info():
    ans = join(PATH, 'info.xml')
    assert exists(ans), ans
    return FileInfo(ans)

@pytest.fixture
def data_info():
    ans = join(PATH, 'info1.xml')
    assert exists(ans), ans
    return DataInfo(ans)

@pytest.fixture
def patient():
    ans = join(PATH, 'subject.xml')
    assert exists(ans), ans
    return Patient(ans)

@pytest.fixture
def sensor_layout():
    ans = join(PATH, 'sensorLayout.xml')
    assert exists(ans), ans
    return SensorLayout(ans)

@pytest.fixture
def coordinates():
    ans = join(PATH, 'coordinates.xml')
    assert exists(ans), ans
    return Coordinates(ans)

@pytest.fixture
def epochs():
    ans = join(PATH, 'epochs.xml')
    assert exists(ans), ans
    return Epochs(ans)

@pytest.fixture
def event_track():
    ans = join(PATH, 'Events_ECI.xml')
    assert exists(ans), ans
    return EventTrack(ans)

"""
Here we start testing the parsed xml files.
"""

def test_FileInfo(file_info):
    assert file_info.version == '3'
    expected_rt = datetime.strptime('2003-04-17T13:35:22.000000-0800', "%Y-%m-%dT%H:%M:%S.%f%z")
    assert file_info.recordTime == expected_rt, "found record time %s [expected %s]"%(file_info.recordTime, expected_rt)


@pytest.mark.parametrize("field,expected", [
    ('channel_type', 'EEG'),
    ('sensorLayoutName', 'Geodesic Sensor Net 256 2.1'),
    ('montageName', 'Geodesic Sensor Net 256 2.1'),
])
def test_DataInfo_generalInfo(field, expected, data_info):
    val = data_info.generalInformation[field]
    assert val == expected, "F[%s] = %s [should be %s]"%(field, val, expected)


@pytest.mark.parametrize("field,expected", [
    ('beginTime', 0),
    ('method', 'Hardware'),
    ('type', 'highpass'),
    ('cutoffFrequency', (0.1, 'Hz')),
])
def test_DataInfo_filters1(field, expected, data_info):
    val = data_info.filters[1][field]
    assert val == expected, "F[%s] = %s [should be %s]"%(field, val, expected)


@pytest.mark.parametrize("field,expected", [
    ('beginTime', 0),
    ('channels', dict([ (1, 0.990157),
                        (10, 1.007665),
                        (249, 0.999596)])),
])
def test_DataInfo_calibrations_GCAL(field, expected, data_info):
    val = data_info.calibrations['GCAL'][field]
    if isinstance(expected, dict):
        for key, exp in expected.items():
            assert val[key] == np.float32(exp), "F[%s][%s] = %s [should be %s]"%(field, key, val[key], exp)
    else:
        assert val == expected, "F[%s] = %s [should be %s]"%(field, val, expected)


@pytest.mark.parametrize("field,expected", [
    ('localIdentifier', 'SE6P1'),
])
def test_subject(field, expected, patient):
    val = patient.fields[field]
    assert val == expected, "subject.fields[%s] = %s [should be %s]"%(field, val, expected)


@pytest.mark.parametrize("prop,idx,expected", [
    ('sensors', 1, {'name': 'None', 'number': 1, 'type': 0, 'x': 415.0, 'y': 147.0, 'z': 0.0}),
    ('sensors', 258, {'name': 'None', 'number': 258, 'type': 2, 'x': 270.0, 'y': 93.0, 'z': 0.0, 'identifier': 1002}),
    ('threads', 0, (1, 2)),
    ('threads', -3, (253, 254)),
    ('tilingSets', 0, list(map(int, "4 7 10 14 17 19 23 27 30 32 35 37 41 44 46 48 51 57 60 62 65 70 73 75 78 86 89 91 93 95 99 107 109 112 114 120 122 124 126 130 141 145 147 150 153 155 160 166 170 172 174 176 184 187 189 191 193 195 198 206 209 212 216 218 222 224 228 236 240 248 251 254 256".split()))),
    ('neighbors', 4, list(map(int, "3 5 11 12 13 226".split()))),
])
def test_SensorLayout(prop, idx, expected, sensor_layout):

    def it(expected):
        """create iterator from iterable `expected`
        
        for dict return `.items()`, else return `enumerate` iterator."""
        if isinstance(expected, dict):
            yield from expected.items()
        elif isinstance(expected, (list, tuple)):
            yield from enumerate(expected)
        else:
            raise ValueError("Error in test {}".format(expected))

    vals = getattr(sensor_layout, prop)[idx]
    for key, exp in it(expected):
        assert vals[key] == exp, "%s[%s][%s] = %s [should be %s]"%(prop, idx, key, vals[key], exp)


def test_Coordinates(coordinates):

    # test parsing of sensor locations and meta info
    for idx, expected in [
        (1, {'name': 'None', 'number': 1, 'type': 0, 'x': np.float32(5.88478), 'y': np.float32(6.51941), 'z': np.float32(-0.247411)}),
        (258, {'name': 'Nasion', 'number': 258, 'type': 2, 'x': 0.0, 'y': np.float32(10.1822), 'z': np.float32(-1.989870), 'identifier': 2002})
    ]:
        sensor = coordinates.sensors[idx]
        for key, exp in expected.items():
            assert sensor[key] == exp, "sensors[%s][%s] = %s [should be %s]"%(idx, key, sensor[key], exp)

    # test parsing of acquiration meta info
    expected = datetime.strptime("2006-04-13T16:00:00.000000-0800", "%Y-%m-%dT%H:%M:%S.%f%z")
    assert coordinates.acqTime == expected, "Acquiration time %s [expected %s]"%(coordinates.acqTime, expected)

    expected = "An Average of Many Data Sets"
    assert coordinates.acqMethod == expected, "Acquiration method '%s' [expected '%s']"%(coordinates.acqMethod, expected)

    assert coordinates.defaultSubject == True, "Default subject not correctly parsed."


@pytest.mark.parametrize("idx,expected", [
    (0, {'beginTime': 0, 'endTime': 216000, 'firstBlock': 1, 'lastBlock': 1}),
    (-2, {'beginTime': 3323676000, 'endTime': 3359904000, 'firstBlock': 184, 'lastBlock': 186}),
])
def test_SensorLayout(idx, expected, epochs):
    vals = epochs.epochs[idx]
    for key, exp in expected.items():
        assert vals[key] == exp, "epochs[%s][%s] = %s [should be %s]"%(idx, key, vals[key], exp)


@pytest.mark.parametrize("idx,expected", [
    (0, {
        'beginTime': datetime.strptime("2003-04-17T13:35:22.032000-0800", "%Y-%m-%dT%H:%M:%S.%f%z"),
        'duration': 1000,
        'code': 'SESS',
        'label': 'SEPlus',
        'description': 'None',
        'sourceDevice': 'Experimental Control Interface',
        'keys': {'age_': 0, 'exp_': 1, 'hand': 0, 'sex_': 0, 'subj': 10, '#cel': 5}
    }),
    (-2, {
        'beginTime': datetime.strptime("2003-04-17T14:32:04.101000-0800", "%Y-%m-%dT%H:%M:%S.%f%z"),
        'duration': 1000,
        'code': 'resp',
        'label': 'None',
        'description': 'None',
        'sourceDevice': 'Experimental Control Interface',
        'keys': {'cel#': 1, 'obs#': 240, 'pos#': 1, 'rsp+': 1}
    }),
])
def test_EventTrack(idx, expected, event_track):
    vals = event_track.events[idx]
    for key, exp in expected.items():
        assert vals[key] == exp, "epochs[%s][%s] = %s [should be %s]"%(idx, key, vals[key], exp)
