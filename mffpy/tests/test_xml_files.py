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
import logging
from io import BytesIO
from os.path import join, dirname, exists
from datetime import datetime
import pytz

import numpy as np
import pytest

from ..xml_files import XML
from ..dict2xml import dict2xml

logging.basicConfig(level=logging.DEBUG)


examples_path = join(dirname(__file__), '..', '..', 'examples')
mff_path = join(examples_path, 'example_1.mff')

"""
Here are several fixtures that parse example xml files
to be tested.  The files parsed are located in `mff_path`.
"""


@pytest.fixture
def file_info():
    ans = join(mff_path, 'info.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


# Data info file for EEG data
@pytest.fixture
def data_info():
    ans = join(mff_path, 'info1.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


# Data info file for PNS data
@pytest.fixture
def data_info2():
    ans = join(examples_path, 'example_3.mff/info2.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


@pytest.fixture
def patient():
    ans = join(mff_path, 'subject.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


@pytest.fixture
def sensor_layout():
    ans = join(mff_path, 'sensorLayout.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


@pytest.fixture
def coordinates():
    ans = join(mff_path, 'coordinates.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


@pytest.fixture
def epochs():
    ans = join(mff_path, 'epochs.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


@pytest.fixture
def event_track():
    ans = join(mff_path, 'Events_ECI.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


@pytest.fixture
def categories():
    ans = join(mff_path, 'categories.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


@pytest.fixture
def dipoleSet():
    ans = join(mff_path, 'dipoleSet.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


@pytest.fixture
def history():
    ans = join(examples_path, 'example_2.mff', 'history.xml')
    assert exists(ans), f"Not found: '{ans}'"
    return XML.from_file(ans)


"""
Here we start testing the parsed xml files.
"""


def test_FileInfo(file_info):
    assert file_info.version == '3'
    expected_rt = datetime.strptime(
        '2003-04-17T13:35:22.000000-0800', "%Y-%m-%dT%H:%M:%S.%f%z")
    assert file_info.recordTime == expected_rt, f"""
    found record time {file_info.recordTime} [expected {expected_rt}]"""


def test_fileInfo_fails():
    """assert that .mff file info expects a timezone"""
    XML.todict('fileInfo', recordTime=datetime.now(tz=pytz.utc))
    with pytest.raises(AssertionError):
        XML.todict('fileInfo', recordTime=datetime.now())


@pytest.mark.parametrize("field,expected", [
    ('channel_type', 'EEG'),
    ('sensorLayoutName', 'Geodesic Sensor Net 256 2.1'),
    ('montageName', 'Geodesic Sensor Net 256 2.1'),
])
def test_DataInfo_generalInfo(field, expected, data_info):
    val = data_info.generalInformation[field]
    assert val == expected, "F[%s] = %s [should be %s]" % (
        field, val, expected)


@pytest.mark.parametrize("field,expected", [
    ('channel_type', 'PNSData'),
    ('pnsSetName', 'Physio 16 set 60hz 1.0'),
])
def test_DataInfo2_generalInfo(field, expected, data_info2):
    val = data_info2.generalInformation[field]
    assert val == expected, "F[%s] = %s [should be %s]" % (
        field, val, expected)


@pytest.mark.parametrize("field,expected", [
    ('beginTime', 0),
    ('method', 'Hardware'),
    ('type', 'highpass'),
    ('cutoffFrequency', (0.1, 'Hz')),
])
def test_DataInfo_filters1(field, expected, data_info):
    val = data_info.filters[1][field]
    assert val == expected, "F[%s] = %s [should be %s]" % (
        field, val, expected)


@pytest.mark.parametrize("field,expected", [
    ('beginTime', 0),
    ('channels', dict([(1, 0.990157),
                       (10, 1.007665),
                       (249, 0.999596)])),
])
def test_DataInfo_calibrations_GCAL(field, expected, data_info):
    val = data_info.calibrations['GCAL'][field]
    if isinstance(expected, dict):
        for key, exp in expected.items():
            assert val[key] == np.float32(exp), f"""
            F[{field}][{key}] = {val[key]} [should be {exp}]"""
    else:
        assert val == expected, "F[%s] = %s [should be %s]" % (
            field, val, expected)


@pytest.mark.parametrize("field,expected", [
    ('localIdentifier', 'SE6P1'),
])
def test_subject(field, expected, patient):
    val = patient.fields[field]
    assert val == expected, "subject.fields[%s] = %s [should be %s]" % (
        field, val, expected)


@pytest.mark.parametrize("prop,idx,expected", [
    ('sensors', 1, {'name': 'None', 'number': 1,
                    'type': 0, 'x': 415.0, 'y': 147.0, 'z': 0.0}),
    ('sensors', 258, {'name': 'None', 'number': 258, 'type': 2,
                      'x': 270.0, 'y': 93.0, 'z': 0.0, 'identifier': 1002}),
    ('threads', 0, (1, 2)),
    ('threads', -3, (253, 254)),
    ('tilingSets', 0, list(map(int, "4 7 10 14 17 19 23 27 30 32 35 37 41 44 \
        46 48 51 57 60 62 65 70 73 75 78 86 89 91 93 95 99 107 109 112 114 \
        120 122 124 126 130 141 145 147 150 153 155 160 166 170 172 174 176 \
        184 187 189 191 193 195 198 206 209 212 216 218 222 224 228 236 240 \
        248 251 254 256".split()))),
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
        assert vals[key] == exp, "%s[%s][%s] = %s [should be %s]" % (
            prop, idx, key, vals[key], exp)


def test_Coordinates(coordinates):

    # test parsing of sensor locations and meta info
    for idx, expected in [
        (1, {'name': 'None', 'number': 1, 'type': 0, 'x': np.float32(5.88478),
             'y': np.float32(6.51941), 'z': np.float32(-0.247411)}),
        (258, {'name': 'Nasion', 'number': 258, 'type': 2, 'x': 0.0, 'y':
               np.float32(10.1822), 'z': np.float32(-1.989870), 'identifier':
               2002})
    ]:
        sensor = coordinates.sensors[idx]
        for key, exp in expected.items():
            assert sensor[key] == exp, f"""
            sensors[{idx}][{key}] = {sensor[key]} [should be {exp}]"""

    # test parsing of acquiration meta info
    expected = datetime.strptime(
        "2006-04-13T16:00:00.000000-0800", "%Y-%m-%dT%H:%M:%S.%f%z")
    assert coordinates.acqTime == expected, f"""
    Acquiration time {coordinates.acqTime} [expected {expected}]"""

    expected = "An Average of Many Data Sets"
    assert coordinates.acqMethod == expected, f"""
    Acquiration method {coordinates.acqMethod} [expected {expected}]"""

    assert coordinates.defaultSubject, "Default subject not correctly parsed."


@pytest.mark.parametrize("idx,expected", [
    (0, {'beginTime': 0, 'endTime': 216000, 'firstBlock': 1, 'lastBlock': 1}),
    (-2, {'beginTime': 3323676000, 'endTime': 3359904000,
          'firstBlock': 184, 'lastBlock': 186}),
])
def test_Epochs(idx, expected, epochs):
    epoch = epochs.epochs[idx]
    for key, exp in expected.items():
        val = getattr(epoch, key)
        assert val == exp, f"""
        epochs[{idx}][{key}] = {val} [should be {exp}]"""


@pytest.mark.parametrize("idx,expected", [
    (0, {
        'beginTime': datetime.strptime("2003-04-17T13:35:22.032000-0800",
                                       "%Y-%m-%dT%H:%M:%S.%f%z"),
        'duration': 1000,
        'code': 'SESS',
        'label': 'SEPlus',
        'description': 'None',
        'sourceDevice': 'Experimental Control Interface',
        'keys': {'age_': 0, 'exp_': 1, 'hand': 0, 'sex_': 0,
                 'subj': 10, '#cel': 5}
    }),
    (-2, {
        'beginTime': datetime.strptime("2003-04-17T14:32:04.101000-0800",
                                       "%Y-%m-%dT%H:%M:%S.%f%z"),
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
        assert vals[key] == exp, f"""
        epochs[{idx}][{key}] = {vals[key]} [should be {exp}]"""


def test_EventTrack_to_xml():
    """Test `EventTrack.content` works with `dict2xml`

    `XML.todict('eventTrack', ..)` accesses `EventTrack.content` to build an
    xml-able dictionary.  We do that in memory using a `BytesIO` stream.  We
    re-read the stream as an `EventTrack` xml file and compare the output with
    our original input.
    """
    # convert some test content into an .xml of type eventTrack
    name = 'testname'
    trackType = 'type of the track'
    events = [
        {
            'beginTime': XML._parse_time_str(
                "2003-04-17T13:35:22.032000-08:00"),
            'duration': 1000,
            'description': 'left eye blink',
            'code': 'LEOG'
        },
        {
            'beginTime': XML._parse_time_str(
                "2003-04-17T13:35:22.032000-08:00"),
            'duration': 1000,
            'description': 'right eye blink',
            'code': 'REOG'
        },
    ]
    track_dict = XML.todict('eventTrack', name=name, trackType=trackType,
                            events=events)
    assert track_dict.pop('filename') == 'Events.xml'
    xml = dict2xml(**track_dict)
    xml_stream = BytesIO()
    xml.write(xml_stream, encoding='UTF-8',
              xml_declaration=True, method='xml')
    xml_stream.seek(0)
    # read the .xml and test content
    output = XML.from_file(xml_stream)
    assert type(output) == type(XML)._tag_registry['eventTrack']
    assert output.name == name
    assert output.trackType == trackType
    assert len(output.events) == len(events)
    for event, expected in zip(events, output.events):
        assert event == expected


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
                1, 12, 15, 17, 18, 19, 25, 31, 32, 34, 35, 37, 45, 46, 49, 55,
                56, 57, 59, 60, 62, 63, 64, 65, 66, 69, 70, 71, 72, 74, 75, 76,
                77, 78, 79, 80, 84, 85, 86, 87, 88, 89, 92, 93, 96, 97, 98, 99,
                100, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112,
                113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124,
                125, 127, 129, 133, 134, 135, 136, 137, 138, 139, 140, 141,
                142, 145, 146, 147, 148, 149, 150, 151, 152, 153, 155, 156,
                157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168,
                169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180,
                181, 182, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195,
                199, 200, 201, 202, 203, 204, 206, 208, 210, 211, 212, 216,
                218, 219, 220, 221, 226, 234, 238, 239, 241, 247, 248, 250,
                251, 253
            ]}],
        'faults': ['eyeb', 'eyem', 'badc']
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
    }
    assert categories['LRND'][0] == expected_LRND0


@pytest.mark.parametrize("idx,expected", [
    (3, {'category': 'ULRN', 't0': 39476000}),
    (-2, {'category': 'LRND', 't0': 3794064000}),
])
def test_sort_categories_by_starttime(categories, idx, expected):
    assert categories.sort_categories_by_starttime()[idx] == expected


def test_Categories_to_xml():
    """Test `Categories.content` works with `dict2xml`"""
    # convert some test content into an .xml of type Categories
    expected_categories = {
        'first category': [
            {
                'status': 'bad',
                'name': 'Average',
                'faults': ['eyeb'],
                'beginTime': 0,
                'endTime': 1200000,
                'evtBegin': 205135,
                'evtEnd': 310153,
                'channelStatus': [
                    {
                        'signalBin': 1,
                        'exclusion': 'badChannels',
                        'channels': [1, 12, 25, 55]
                    }
                ],
                'keys': {
                    '#seg': {
                        'type': 'long',
                        'data': 3
                    },
                    'subj': {
                        'type': 'person',
                        'data': 'RM271_noise_test'
                    }
                }
            }
        ],
    }
    categories_dict = XML.todict('categories', categories=expected_categories)
    assert categories_dict.pop('filename') == 'categories.xml'
    xml = dict2xml(**categories_dict)
    xml_stream = BytesIO()
    xml.write(xml_stream, encoding='UTF-8',
              xml_declaration=True, method='xml')
    xml_stream.seek(0)
    # read the .xml and test content
    output = XML.from_file(xml_stream)
    assert type(output) == type(XML)._tag_registry['categories']
    categories = output.categories
    for name, category in categories.items():
        expected_category = expected_categories[name]
        for segment, expected in zip(category, expected_category):
            for key in segment.keys():
                assert segment[key] == expected[key]


def test_dipoleSet(dipoleSet):
    assert dipoleSet.name == 'SWS_003_IHM', dipoleSet.name
    assert dipoleSet.type == 'Dense', dipoleSet.type
    assert len(dipoleSet) == 4, f"found {len(dipoleSet)}"
    assert dipoleSet.computationCoordinate == pytest.approx(np.array([
        [64, 120, 150],
        [68, 120, 150],
        [69, 120, 150],
        [61, 130, 150]
    ], dtype=np.float32))
    assert dipoleSet.visualizationCoordinate == pytest.approx(np.array([
        [61, 140, 150],
        [65, 140, 160],
        [66, 140, 150],
        [59, 140, 150]
    ], dtype=np.float32))
    assert dipoleSet.orientationVector == pytest.approx(np.array([
        [0.25, 0.35, 0.9],
        [-0.05, 0.91, 0.4],
        [0.6, -0.0047, 0.8],
        [0.61, 0.44, 0.66]
    ], dtype=np.float32))


def test_dipoleSet_w_different_order(dipoleSet):
    """test reading `computationCoordinate` with different order"""
    assert dipoleSet.computationCoordinate == pytest.approx(np.array([
        [64, 120, 150],
        [68, 120, 150],
        [69, 120, 150],
        [61, 130, 150]
    ], dtype=np.float32))


@pytest.mark.parametrize("idx,expected", [
    ('name', 'Noise_30Seconds'),
    ('method', 'Segmentation'),
    ('version', '5.4.1.2'),
    ('beginTime', XML._parse_time_str('2019-10-25T12:09:57.639365-07:00')),
    ('endTime', XML._parse_time_str('2019-10-25T12:09:57.897929-07:00')),
    ('sourceFiles', ['/Volumes/PARTYONWAYN/NoiseTest_2.mff']),
])
def test_history(history, idx, expected):
    """test parsing of `history.xml`"""
    assert len(history) == 1
    entry = history[0]
    assert entry[idx] == expected
    assert len(entry['settings']) == 6
    assert len(entry['results']) == 2
    assert history.mff_flavor() == 'segmented'


def test_history_to_xml():
    """test `History.content` works with `dict2xml`

    We write a formatted dictionary with the contents of a history.xml
    file to a `BytesIO` stream. We then read the stream as a `History`
    object and check `History.entries` against the original input.
    """
    entries = [
        {
            'name': 'seg tool',
            'method': 'Segmentation',
            'version': 'NS Version',
            'beginTime': XML._parse_time_str(
                '2020-08-27T13:32:26.008693-07:00'),
            'endTime': XML._parse_time_str(
                '2020-08-27T13:32:26.113988-07:00'),
            'sourceFiles': ['file/path.mff'],
            'settings': ['Setting 1', 'Setting 2'],
            'results': ['Result', 'Result']
        },
        {
            'name': 'ave tool',
            'method': 'Averaging',
            'version': 'NS Version',
            'beginTime': XML._parse_time_str(
                '2020-08-27T13:33:08.945341-07:00'),
            'endTime': XML._parse_time_str(
                '2020-08-27T13:33:09.006109-07:00'),
            'sourceFiles': ['file/path.mff'],
            'settings': ['Setting 1', 'Setting 2'],
            'results': ['Result', 'Result']
        }
    ]
    history_content = XML.todict('historyEntries', entries=entries)
    assert history_content.pop('filename') == 'history.xml'
    xml = dict2xml(**history_content)
    xml_stream = BytesIO()
    xml.write(xml_stream, encoding='UTF-8',
              xml_declaration=True, method='xml')
    xml_stream.seek(0)
    output = XML.from_file(xml_stream)
    assert type(output) == type(XML)._tag_registry['historyEntries']
    assert len(output) == len(entries)
    for entry, expected in zip(entries, output.entries):
        assert entry == expected
