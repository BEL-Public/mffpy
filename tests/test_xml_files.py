
# B/c the module is not compiled we can import the current version
from sys import path
from os.path import join, exists, dirname
path.insert(0, join(dirname(__file__),'..'))

import pytest
import numpy as np
from mffpy.io.egi.xml_files import FileInfo, DataInfo

PATH = join(dirname(__file__), '..', 'examples', 'example_1.mff')

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


def test_FileInfo(file_info):
    assert file_info.version == '3'
    assert file_info.recordTime == '2003-04-17T13:35:22.000000-08:00'

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
