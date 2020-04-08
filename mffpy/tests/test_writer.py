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
from datetime import datetime
from os import makedirs, rmdir, remove
from os.path import join
from shutil import rmtree

import pytest
import json
import numpy as np

from ..writer import Writer
from ..bin_writer import BinWriter, StreamingBinWriter
from ..reader import Reader
from ..xml_files import XML


def test_writer_receives_bad_init_data():
    """Test bin writer fails when initialized with non-int sampling rate"""
    BinWriter(100)
    with pytest.raises(AssertionError):
        BinWriter(100.0)


def test_writer_doesnt_overwrite():
    dirname = 'testdir.mff'
    makedirs(dirname)
    with pytest.raises(AssertionError):
        Writer(dirname)
    rmdir(dirname)


def test_writer_writes():
    dirname = 'testdir2.mff'
    # create some data and add it to a binary writer
    device = 'HydroCel GSN 256 1.0'
    num_samples = 10
    num_channels = 256
    sampling_rate = 128
    b = BinWriter(sampling_rate=sampling_rate, data_type='EEG')
    data = np.random.randn(num_channels, num_samples).astype(np.float32)
    b.add_block(data)
    # create an mffpy.Writer and add a file info, and the binary file
    W = Writer(dirname)
    startdatetime = datetime.strptime(
        '1984-02-18T14:00:10.000000+0100', XML._time_format)
    W.addxml('fileInfo', recordTime=startdatetime)
    W.add_coordinates_and_sensor_layout(device)
    W.addbin(b)
    W.write()
    # read it again; compare the result
    R = Reader(dirname)
    assert R.startdatetime == startdatetime
    # Read binary data and compare
    read_data = R.get_physical_samples_from_epoch(R.epochs[0])
    assert 'EEG' in read_data
    read_data, t0 = read_data['EEG']
    assert t0 == 0.0
    assert read_data == pytest.approx(data)
    layout = R.directory.filepointer('sensorLayout')
    layout = XML.from_file(layout)
    assert layout.name == device
    # cleanup
    try:
        remove(join(dirname, 'info.xml'))
        remove(join(dirname, 'info1.xml'))
        remove(join(dirname, 'epochs.xml'))
        remove(join(dirname, 'signal1.bin'))
        remove(join(dirname, 'coordinates.xml'))
        remove(join(dirname, 'sensorLayout.xml'))
        rmdir(dirname)
    except BaseException:
        raise AssertionError(f"""
        Clean-up failed of '{dirname}'.  Were additional files written?""")


def test_writer_exports_JSON():
    filename = 'test1.json'
    # Root tags corresponding to available XMLType sub-classes
    xml_root_tags = ['fileInfo', 'dataInfo', 'patient', 'sensorLayout',
                     'coordinates', 'epochs', 'eventTrack', 'categories',
                     'dipoleSet']
    # create an empty sample dictionary for each root tag
    content = {tag: {} for tag in xml_root_tags}
    # Add extra info to the dictionary
    content['samplingRate'] = 128
    content['durations'] = 1.0
    content['units'] = 'uV'
    content['numChannels'] = 256
    # create an mffpy.Writer and export data to a .json file
    W = Writer(filename)
    W.export_to_json(content)
    # read it again; compare the result
    with open(filename) as file:
        data = json.load(file)
    assert data == content
    # cleanup
    try:
        remove(filename)
    except BaseException:
        raise AssertionError(f"""Clean-up failed of '{filename}'.""")

def test_streaming_writer_receives_bad_init_data():
    """Test bin writer fails when initialized with non-int sampling rate"""
    dirname = 'testdir.mff'
    makedirs(dirname)
    StreamingBinWriter(100, mffdir=dirname)
    with pytest.raises(AssertionError):
        StreamingBinWriter(100.0, mffdir=dirname)
    rmtree(dirname)

def test_streaming_writer_writes():
    dirname = 'testdir3.mff'
    # create some data and add it to a binary writer
    device = 'HydroCel GSN 256 1.0'
    num_samples = 10
    num_channels = 256
    sampling_rate = 128
    # create an mffpy.Writer and add a file info, and the binary file
    writer = Writer(dirname)
    writer.create_directory()
    bin_writer = StreamingBinWriter(sampling_rate=sampling_rate, data_type='EEG', mffdir=dirname)
    data = np.random.randn(num_channels, num_samples).astype(np.float32)
    bin_writer.add_block(data)
    startdatetime = datetime.strptime(
        '1984-02-18T14:00:10.000000+0100', XML._time_format)
    writer.addxml('fileInfo', recordTime=startdatetime)
    writer.add_coordinates_and_sensor_layout(device)
    writer.addbin(bin_writer)
    writer.write()
    # read it again; compare the result
    reader = Reader(dirname)
    assert reader.startdatetime == startdatetime
    # Read binary data and compare
    read_data = reader.get_physical_samples_from_epoch(reader.epochs[0])
    assert 'EEG' in read_data
    read_data, t0 = read_data['EEG']
    assert t0 == 0.0
    assert read_data == pytest.approx(data)
    layout = reader.directory.filepointer('sensorLayout')
    layout = XML.from_file(layout)
    assert layout.name == device
    # cleanup
    try:
        rmtree(dirname)
    except BaseException:
        raise AssertionError(f"""
        Clean-up failed of '{dirname}'.  Were additional files written?""")
