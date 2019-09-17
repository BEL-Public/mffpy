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

from cached_property import cached_property

from . import xml_files
from .xml_files import XML
from . import bin_files
from .mffdir import get_directory


class Reader:
    """
    Create an .mff reader

    class `Reader` is the main entry point to `mffpy`'s functionality.

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
    def epochs(self) -> xml_files.Epochs:
        with self.directory.filepointer('epochs') as fp:
            epochs = XML.from_file(fp)
        assert isinstance(epochs, xml_files.Epochs), f"""
        .xml file 'epochs.xml' of wrong type {type(epochs)}"""
        return epochs.epochs

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

    @cached_property
    def _blobs(self) -> Dict[str, bin_files.BinFile]:
        """return dictionary of `BinFile` data readers by signal type"""
        __blobs = {}
        for si in self.directory.signals_with_info():
            with self.directory.filepointer(si.info) as fp:
                info = XML.from_file(fp)
            bf = bin_files.BinFile(si.signal, info)
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
