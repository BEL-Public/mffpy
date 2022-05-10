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
from os import makedirs, listdir
from os.path import join, splitext

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
    with pytest.raises(AssertionError) as exc_info:
        BinWriter(100.0)
    assert str(exc_info.value) == "Sampling rate not int. Received 100.0"


def test_writer_doesnt_overwrite(tmpdir):
    """test that `mffpy.Writer` doesn't overwrite existing files by default"""
    dirname = join(str(tmpdir), 'testdir.mff')
    makedirs(dirname, exist_ok=True)
    with pytest.raises(AssertionError, match='File.*exists already'):
        Writer(dirname)


def test_writer_writes(tmpdir):
    """Test `mffpy.Writer` can write binary and xml files"""
    dirname = join(str(tmpdir), 'testdir2.mff')
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


def test_writer_can_overwrite(tmpdir):
    """test that the Writer does overwrite existing files"""
    dirname = join(str(tmpdir), 'testdir2.mff')
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

    # list files
    files = listdir(dirname)
    assert 'info.xml' in files
    assert 'coordinates.xml' in files
    assert 'sensorLayout.xml' in files

    # add a directory inside
    makedirs(join(dirname, 'test'))

    # create new writer to overwrite
    b = BinWriter(sampling_rate=sampling_rate, data_type='EEG')
    data2 = np.random.randn(num_channels, num_samples).astype(np.float32)
    b.add_block(data2)
    W = Writer(dirname, overwrite=True)
    W.addbin(b)
    W.write()

    # compare files with
    files = listdir(dirname)
    assert 'info.xml' not in files
    assert 'coordinates.xml' not in files
    assert 'sensorLayout.xml' not in files
    assert 'test' not in files

    # read
    R = Reader(dirname)
    with pytest.raises(FileNotFoundError):
        R.startdatetime
    with pytest.raises(FileNotFoundError):
        R.directory.filepointer('sensorLayout')
    read_data = R.get_physical_samples_from_epoch(R.epochs[0])
    assert 'EEG' in read_data
    read_data, t0 = read_data['EEG']
    assert t0 == 0.0
    assert np.allclose(read_data, data2)
    assert not np.allclose(read_data, data)

    # test writer can 'overwrite' if there is nothing to overwrite
    dirname = join(str(tmpdir), 'testdir3.mff')
    W = Writer(dirname, overwrite=True)
    W.addbin(b)
    W.write()


def test_overwrite_mfz(tmpdir):
    """Test mffdir and mfz file are overwritten when overwrite is on"""
    mfzpath = join(tmpdir, 'test.mfz')
    mffpath = splitext(mfzpath)[0] + '.mff'
    time1 = datetime.strptime('1984-02-18T14:00:10.000000+0100',
                              "%Y-%m-%dT%H:%M:%S.%f%z")
    time2 = datetime.strptime('1973-10-23T14:00:10.000000+0100',
                              "%Y-%m-%dT%H:%M:%S.%f%z")

    W1 = Writer(mfzpath)
    W1.addxml('fileInfo', recordTime=time1)
    W1.write()

    for p in [mffpath, mfzpath]:
        R1 = Reader(p)
        assert R1.startdatetime == time1

    W2 = Writer(mfzpath, overwrite=True)
    W2.addxml('fileInfo', recordTime=time2)
    W2.write()

    for p in [mffpath, mfzpath]:
        R2 = Reader(p)
        assert R2.startdatetime == time2


def test_writer_writes_multple_bins(tmpdir):
    """test that `mffpy.Writer` can write multiple binary files"""
    dirname = join(str(tmpdir), 'multiple_bins.mff')
    device = 'HydroCel GSN 256 1.0'
    # create some data and add it to binary writers
    num_samples = 10
    sampling_rate = 128
    num_channels_dict = {
        'EEG': 256,
        'PNSData': 16
    }
    data = {
        dtype: np.random.randn(
            num_channels, num_samples).astype(np.float32)
        for dtype, num_channels in num_channels_dict.items()
    }
    bin_writers = {
        dtype: BinWriter(sampling_rate=sampling_rate, data_type=dtype)
        for dtype, num_channels in num_channels_dict.items()
    }
    for dtype, bin_writer in bin_writers.items():
        bin_writer.add_block(data[dtype])
    # create an mffpy.Writer and add a file info, and the binary file
    W = Writer(dirname)
    startdatetime = datetime.strptime(
        '1984-02-18T14:00:10.000000+0100', XML._time_format)
    W.addxml('fileInfo', recordTime=startdatetime)
    W.add_coordinates_and_sensor_layout(device)
    for b in bin_writers.values():
        W.addbin(b)

    W.write()
    # read it again; compare the result
    R = Reader(dirname)
    assert R.startdatetime == startdatetime
    # Read binary data and compare
    written_data = R.get_physical_samples_from_epoch(R.epochs[0])
    for dtype, expected in data.items():
        assert dtype in written_data
        written, t0 = written_data[dtype]
        assert t0 == 0.0
        assert written == pytest.approx(expected)

    layout = R.directory.filepointer('sensorLayout')
    layout = XML.from_file(layout)
    assert layout.name == device


def test_write_multiple_blocks():
    """check that BinWriter correctly handles adding multiple blocks"""
    B = BinWriter(sampling_rate=250)
    data = np.random.randn(257, 10).astype(np.float32)
    B.add_block(data)
    B.add_block(data, offset_us=None)
    assert len(B.epochs) == 1
    B.add_block(data, offset_us=0)
    assert len(B.epochs) == 2
    with pytest.raises(ValueError) as exc_info:
        B.add_block(data, offset_us=-1)
    assert str(exc_info.value) == 'offset_us cannot be negative. Got: -1.'


def test_writer_is_compatible_with_egi():
    """check that binary writers fail to write EGI-incompatible files"""
    filename = 'unimportant-filename.mff'
    bin_writer = BinWriter(sampling_rate=128, data_type='PNSData')
    writer = Writer(filename)
    message = "Writing type 'PNSData' to 'signal1.bin' may be " \
              "incompatible with EGI software.\nTo ignore this error " \
              "set:\n\n\tBinWriter._compatible = False"
    with pytest.raises(ValueError) as exc_info:
        writer.addbin(bin_writer)
    assert str(exc_info.value) == message

    with pytest.raises(ValueError) as exc_info:
        StreamingBinWriter(100, data_type='PNSData', mffdir=filename)
    assert str(exc_info.value) == message


def test_writer_exports_JSON(tmpdir):
    filename = join(str(tmpdir), 'test1.json')
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


def test_streaming_writer_receives_bad_init_data(tmpdir):
    """Test bin writer fails when initialized with non-int sampling rate"""
    dirname = join(str(tmpdir), 'testdir.mff')
    makedirs(dirname)
    StreamingBinWriter(100, mffdir=dirname)
    with pytest.raises(AssertionError) as exc_info:
        StreamingBinWriter(100.0, mffdir=dirname)
    assert str(exc_info.value) == "Sampling rate not int. Received 100.0"


def test_streaming_writer_writes(tmpdir):
    dirname = join(str(tmpdir), 'testdir3.mff')
    # create some data and add it to a binary writer
    device = 'HydroCel GSN 256 1.0'
    num_samples = 10
    num_channels = 256
    sampling_rate = 128
    # create an mffpy.Writer and add a file info, and the binary file
    writer = Writer(dirname)
    writer.create_directory()
    bin_writer = StreamingBinWriter(
        sampling_rate=sampling_rate, data_type='EEG', mffdir=dirname)
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
