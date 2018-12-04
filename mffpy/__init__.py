
from . import xml_files
from . import bin_files
from .mffdir import MFFDirectory
from .cached_property import cached_property

class Reader(MFFDirectory):
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

    @cached_property
    def sampling_rates(self):
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
    def durations(self):
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
    def startdatetime(self):
        """
        ```python
        Reader.startdatetime
        ```
        UTC start date and time of the recording

        Return UTC start date and time of the recording.  The
        returned object is of type `datetime.datetime`.
        """
        info = xml_files.open(self.filename('info'))
        return info.recordTime

    @property
    def units(self):
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
    def num_channels(self):
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
    def _blobs(self):
        """return dictionary of `BinFile` data readers by signal type"""
        __blobs = {}
        for si in self.signals_with_info():
            bf = bin_files.BinFile(si.signal, si.info)
            __blobs[bf.signal_type] = bf
        return __blobs

    def set_unit(self, channel_type, unit):
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

    def set_calibration(self, channel_type, cal):
        """set calibration of a channel type"""
        self._blobs[channel_type].calibration = cal

    def get_physical_samples(self, t0=0.0, dt=None, channels=None, block_slice=None):
        """return signal data in the range `(t0, t0+dt)` in seconds from `channels`
        """
        if channels is None:
            channels = list(self._blobs.keys())

        return {
            typ: blob.get_physical_samples(t0, dt, block_slice=block_slice)
            for typ, blob in self._blobs.items()
            if typ in channels
        }

    def get_physical_samples_from_epoch(self, epoch, t0=0.0, dt=None, channels=None):
        """
        return samples by channels of an epoch

        Returns a `dict` of signal samples by channel names given in a list
        `channels`.  The samples will be in the range `(t0, t0+dt)` taken
        relative to `epoch.t0`.

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
        X = fo.read_physical_samples_from_epoch(fo.epochs[0])
        ```
        """
        assert isinstance(epoch, xml_files.Epoch), "argument epoch of type %s [requires %s]"%(type(epoch), xml_files.Epoch)
        assert t0 >= 0.0, "Only positve `t0` allowed [%s]"%t0
        dt = dt if dt is None or 0.0 < dt < epoch.dt-t0 else None
        return self.get_physical_samples(
                t0, dt, channels, block_slice=epoch.block_slice)
