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
from typing import Tuple, Dict, List

import numpy as np

from .cached_property import cached_property

from . import xml_files
from .xml_files import XML, Categories, Epochs
from . import bin_files
from .mffdir import get_directory
from base64 import b64encode


def object_to_bytes(object, encoding='utf-8'):
    """
    Translate an object into its string form
    and then convert that string into its raw bytes form.
    :param object: An object to convert into a bytes literal.
    :param encoding: A string value indicating the encoding to use.
                     Defaults to 'utf-8'.
    :return: the converted bytes object.
    """
    return bytes(str(object), encoding=encoding)


class Reader:
    """
    Create an .mff reader

    class `Reader` is the main entry point to `mffpy`'s functionality.

    :throws: ValueError if the passed filename
             does not point to a valid MFF file.

    Example use:
    ```python
    import mffpy
    fo = mffpy.Reader('./examples/example_1.mff')
    fo.set_unit('EEG', 'uV')
    X = fo.read_physical_samples_from_epoch(
            fo.epochs[0], channels=['EEG'])
    ```
    """

    def __init__(self, filename: str):
        self.directory = get_directory(filename)

    @cached_property
    def flavor(self) -> str:
        """
        ```python
        Reader.flavor
        ```
        return flavor of the MFF

        Return string value with the flavor of the MFF either, 'continuous',
        'segmented', or 'averaged'. This is determined from the entries in
        the `history.xml` file. If no `history.xml` return 'continuous'.
        """
        if 'history.xml' in self.directory.listdir():
            with self.directory.filepointer('history') as fp:
                history = XML.from_file(fp)
                return history.mff_flavor()
        else:
            return 'continuous'

    @cached_property
    def categories(self) -> Categories:
        """
        ```python
        Reader.categories
        ```
        categories present in a loaded MFF file

        Return dictionary of categories names and the segments of
        data associated with each category. If this is a continuous
        MFF file, this method results in a ValueError.
        """
        with self.directory.filepointer('categories') as fp:
            categories = XML.from_file(fp)
        assert isinstance(categories, xml_files.Categories), f"""
            .xml file 'categories.xml' of wrong type {type(categories)}"""
        return categories

    @cached_property
    def epochs(self) -> Epochs:
        """
        ```python
        Reader.epochs
        ```
        return all epochs in MFF file

        Return a list of `epoch.Epoch` objects containing information
        about each epoch in the MFF file. If categories information
        is present, this is used to fill in `Epoch.name` for each epoch.
        """
        with self.directory.filepointer('epochs') as fp:
            epochs = XML.from_file(fp)
        assert isinstance(epochs, xml_files.Epochs), f"""
            .xml file 'epochs.xml' of wrong type {type(epochs)}"""
        # Attempt to add category names to the `Epoch` objects in `epochs`
        try:
            categories = self.categories
        except (ValueError, AssertionError):
            print('categories.xml not found or of wrong type. '
                  '`Epoch.name` will default to "epoch" for all epochs.')
            return epochs
        # Sort category info by start time of each block
        epochs.associate_categories(categories)
        return epochs

    @cached_property
    def sampling_rates(self) -> Dict[str, float]:
        """
        ```python
        Reader.sampling_rates
        ```
        sampling rates by channel type

        Return dictionary of sampling rate by channel type.  Each
        sampling rate is returned in Hz as a float.
        """
        return {
            fn: bin_file.sampling_rate
            for fn, bin_file in self._blobs.items()
        }

    @cached_property
    def durations(self) -> Dict[str, float]:
        """
        ```python
        Reader.durations
        ```
        recorded durations by channel type

        Return dictionary of duration by channel type.  Each
        duration is returned in seconds as a float.
        """
        return {
            fn: bin_file.duration
            for fn, bin_file in self._blobs.items()
        }

    @cached_property
    def startdatetime(self) -> datetime:
        """
        ```python
        Reader.startdatetime
        ```
        UTC start date and time of the recording

        Return UTC start date and time of the recording.  The
        returned object is of type `datetime.datetime`.
        """
        with self.directory.filepointer('info') as fp:
            info = XML.from_file(fp)
        assert isinstance(info, xml_files.FileInfo), f"""
        .xml file 'info.xml' of wrong type {type(info)}"""
        return info.recordTime

    @property
    def units(self) -> Dict[str, str]:
        """
        ```python
        Reader.units
        ```

        Return dictionary of units by channel type.  Each unit is returned as a
        `str` of SI units (micro: `'u'`).
        """
        return {
            fn: bin_file.unit
            for fn, bin_file in self._blobs.items()
        }

    @cached_property
    def num_channels(self) -> Dict[str, int]:
        """
        ```python
        Reader.num_channels
        ```

        Return dictionary of number of channels by channel type.  Each
        number is returned as an `int`.
        """
        return {
            fn: bin_file.num_channels
            for fn, bin_file in self._blobs.items()
        }

    @property
    def _blobs(self) -> Dict[str, bin_files.BinFile]:
        """return dictionary of `BinFile` data readers by signal type"""
        __blobs = {}
        for si in self.directory.signals_with_info():
            with self.directory.filepointer(si.info) as fp:
                info = XML.from_file(fp)
            bf = bin_files.BinFile(si.signal, info,
                                   info.generalInformation['channel_type'])
            __blobs[bf.signal_type] = bf
        return __blobs

    def set_unit(self, channel_type: str, unit: str):
        """set output units for a type of channels

        Set physical unit of a channel type.  The allowed conversion
        values for `unit` depend on the original unit.  We allow all
        combinations of conversions of 'V', 'mV', 'uV'.

        **Arguments**

        * **`channel_type`**: `str` with the channel type.
        * **`unit`**: `str` with the unit you would like to convert to.

        **Example use**

        ```python
        import mffpy
        fo = mffpy.Reader('./examples/example_1.mff')
        fo.set_unit('EEG', 'uV')
        ```
        """
        self._blobs[channel_type].unit = unit

    def set_calibration(self, channel_type: str, cal: str):
        """set calibration of a channel type"""
        self._blobs[channel_type].calibration = cal

    def get_physical_samples(self, t0: float = 0.0, dt: float = None,
                             channels: List[str] = None,
                             block_slice: slice = None
                             ) -> Dict[str, Tuple[np.ndarray, float]]:
        """return signal data in the range `(t0, t0+dt)` in seconds from `channels`

        Use `get_physical_samples_from_epoch` instead."""
        if channels is None:
            channels = list(self._blobs.keys())

        return {
            typ: blob.get_physical_samples(t0, dt, block_slice=block_slice)
            for typ, blob in self._blobs.items()
            if typ in channels
        }

    def get_physical_samples_from_epoch(self, epoch: xml_files.Epoch,
                                        t0: float = 0.0, dt: float = None,
                                        channels: List[str] = None
                                        ) -> Dict[str,
                                                  Tuple[np.ndarray, float]]:
        """
        return samples and start time by channels of an epoch

        Returns a `dict` of tuples of [0] signal samples by channel names given
        and [1] the start time in seconds, with keys from the list `channels`.
        The samples will be in the range `(t0, t0+dt)` taken relative to
        `epoch.t0`.

        **Arguments**

        * **`epoch`**: `xml_files.Epoch` from which you would like to get data.

        * **`t0`**: `float` with relative offset in seconds into the data from
        epoch start.

        * **`dt`**: `float` with requested signal duration in seconds.  Value
        `None` defaults to maximum starting at `t0`.

        * **`channels`**: `list` of channel-type `str` each of which will be a
        key in the returned `dict`.  `None` defaults to all available channels.

        **Note**

        * The start time of the returned data is `epoch.t0` seconds from
        recording start.

        * Only the epoch data can be requested.  If you want to pad these, do
        it yourself.

        * No interpolation will be performed to correct for the fact that `t0`
        falls in between samples.

        **Example use**

        ```python
        import mffpy
        fo = mffpy.Reader('./examples/example_1.mff')
        X = fo.read_physical_samples_from_epoch(fo.epochs[0], t0, dt)
        eeg, t0_eeg = X['EEG']
        ```
        """
        assert isinstance(epoch, xml_files.Epoch), f"""
        argument epoch of type {type(epoch)} [requires {xml_files.Epoch}]"""
        assert t0 >= 0.0, "Only non-negative `t0` allowed [%s]" % t0
        dt = dt if dt is None or 0.0 < dt < epoch.dt-t0 else None
        return self.get_physical_samples(
            t0, dt, channels, block_slice=epoch.block_slice)

    def get_mff_content(self):
        """return the content of an mff file.

        The output of this function is supposed to return a dictionary
        containing one serializable object per valid .xml file. Valid
        .xml files are those whose types belongs to one of the available
        XMLType sub-classes.

        **Returns**
        mff_content: dict
            dictionary containing the content of an mff file.
        """

        # Root tags corresponding to available XMLType sub-classes
        xml_root_tags = xml_files.XMLType.xml_root_tags()
        # Create the dictionary that will be returned by this function
        mff_content = {tag: {} for tag in xml_root_tags}

        # Iterate over existing .xml files
        for xmlfile in self.directory.files_by_type['.xml']:
            with self.directory.filepointer(xmlfile) as fp:
                try:
                    obj = XML.from_file(fp)
                    content = obj.get_serializable_content()

                    if obj.xml_root_tag == 'categories':
                        # Add EEG data to each segment of each category
                        for category in content['categories'].values():
                            # Iterate over each segment
                            for segment in category:
                                # Multiply time values by 1e-6
                                # because "get_physical_samples" function
                                # expects time values to be in seconds.
                                t0 = segment['beginTime'] * 1e-6
                                dt = (segment['endTime'] -
                                      segment['beginTime']) * 1e-6
                                # Get samples from current segment
                                samples = self.get_physical_samples(
                                    t0=t0, dt=dt, channels=['EEG'])
                                eeg, start_time = samples['EEG']
                                # Insert an EEG data field into each segment.
                                # Compress EEG data using a
                                # base64 encoding scheme.
                                segment['eegData'] = str(
                                    b64encode(object_to_bytes(eeg.tolist())),
                                    encoding='utf-8')

                    mff_content[obj.xml_root_tag] = content
                except KeyError as e:
                    print(f'{e} is not one of the valid .xml types')

        # Add extra info to the returned dictionary
        mff_content['samplingRate'] = self.sampling_rates['EEG']
        mff_content['durations'] = self.durations['EEG']
        mff_content['units'] = self.units['EEG']
        mff_content['numChannels'] = self.num_channels['EEG']

        return mff_content
