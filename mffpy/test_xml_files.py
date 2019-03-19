
import logging
logging.basicConfig(level=logging.DEBUG)

import pytest
import numpy as np
from .xml_files import XML
from datetime import datetime
from os.path import join, dirname, exists

examples_path = join(dirname(__file__), '..', 'examples')
mff_path = join(examples_path, 'example_1.mff')

"""
Here are several fixtures that parse example xml files
to be tested.  The files parsed are located in `mff_path`.
"""

@pytest.fixture
def file_info():
    ans = join(mff_path, 'info.xml')
    assert exists(ans), ans
    return XML.from_file(ans)

@pytest.fixture
def data_info():
    ans = join(mff_path, 'info1.xml')
    assert exists(ans), ans
    return XML.from_file(ans)

@pytest.fixture
def patient():
    ans = join(mff_path, 'subject.xml')
    assert exists(ans), ans
    return XML.from_file(ans)

@pytest.fixture
def sensor_layout():
    ans = join(mff_path, 'sensorLayout.xml')
    assert exists(ans), ans
    return XML.from_file(ans)

@pytest.fixture
def coordinates():
    ans = join(mff_path, 'coordinates.xml')
    assert exists(ans), ans
    return XML.from_file(ans)

@pytest.fixture
def epochs():
    ans = join(mff_path, 'epochs.xml')
    assert exists(ans), ans
    return XML.from_file(ans)

@pytest.fixture
def event_track():
    ans = join(mff_path, 'Events_ECI.xml')
    assert exists(ans), ans
    return XML.from_file(ans)

@pytest.fixture
def categories():
    ans = join(mff_path, 'categories.xml')
    assert exists(ans), ans
    return XML.from_file(ans)

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
def test_Epochs(idx, expected, epochs):
    epoch = epochs.epochs[idx]
    for key, exp in expected.items():
        val = getattr(epoch, key)
        assert val == exp, "epochs[%s][%s] = %s [should be %s]"%(idx, key, val, exp)


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

def test_Categories(categories):
    assert all(k in categories for k in ('ULRN', 'LRND'))
    assert len(categories['ULRN']) == 50
    assert len(categories['LRND']) == 19
    expected_ULRN0 = {
        'status': 'bad',
        'beginTime': 0,
        'endTime': 1200000,
        'evtBegin': 201981,
        'evtEnd': 201981,
        'channelStatus': [{
        'signalBin': 1,
        'exclusion': 'badChannels',
        'channels': [
            1, 12, 15, 17, 18, 19, 25, 31, 32, 34, 35, 37, 45, 46, 49, 55, 56, 57, 59, 60,
            62, 63, 64, 65, 66, 69, 70, 71, 72, 74, 75, 76, 77, 78, 79, 80, 84, 85, 86, 87,
            88, 89, 92, 93, 96, 97, 98, 99, 100, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112,
            113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 127, 129, 133, 134, 135, 136, 137,
            138, 139, 140, 141, 142, 145, 146, 147, 148, 149, 150, 151, 152, 153, 155, 156, 157, 158, 159, 160,
            161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180,
            181, 182, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 199, 200, 201, 202, 203, 204, 206, 208,
            210, 211, 212, 216, 218, 219, 220, 221, 226, 234, 238, 239, 241, 247, 248, 250, 251, 253
        ]}],
        'keys': None, 'faults': ['eyeb', 'eyem', 'badc']
    }
    assert categories['ULRN'][0] == expected_ULRN0
    expected_LRND0 = {
        'status': 'good',
        'beginTime': 3655704000,
        'endTime': 3656904000,
        'evtBegin': 3655907981,
        'evtEnd': 3655907981,
        'channelStatus': [{'signalBin': 1,
        'exclusion': 'badChannels',
        'channels': []}],
        'keys': None,
        'faults': []
    }
    assert categories['LRND'][0] == expected_LRND0
