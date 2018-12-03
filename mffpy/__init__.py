
from . import xml_files
from . import bin_files
from .mffdir import MFFDirectory
from .cached_property import cached_property

class Reader(MFFDirectory):
    """
    A class to read signal data in .mff format.

    Attributes
    ----------
    sampling_rates : `dict` of `float`
        sampling rate in Hz by channel type
    durations : `dict` of `float`
        duration in seconds by channel type
    startdatetime : `datetime.datetime`
        UTC start date and time of the recording

    Methods
    -------
    set_unit(channel_type, unit)
        set the physical unit of channel type
    set_calibration(channel_type, cal)
        set the calibration of channel type
    get_physical_samples(t0=0.0, dt=None, channels=None, block_slice=None)
        return physical samples fo specified channels in the range t0 ->
        t0+dt (in seconds).
    get_physical_samples_from_epoch(epoch, t0=0.0, dt=None, channels=None)
        return physical samples fo specified channels in the range t0 ->
        t0+dt (in seconds).  t0 is offset by the epoch start.
    """

    @cached_property
    def sampling_rates(self):
        """sampling rates by channel type"""
        return {
            fn: bin_file.sampling_rate
            for fn, bin_file in self._blobs.items()
        }

    @cached_property
    def durations(self):
        """recorded durations by channel type"""
        return {
            fn: bin_file.duration
            for fn, bin_file in self._blobs.items()
        }

    @cached_property
    def startdatetime(self):
        """UTC start time of the recording"""
        info = xml_files.open(self.filename('info'))
        return info.recordTime

    @cached_property
    def num_channels(self):
        """sampling rates by channel type"""
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
        """set physical unit of a channel type"""
        self._blobs[channel_type].unit = unit

    def set_calibration(self, channel_type, cal):
        """set calibration of a channel type"""
        self._blobs[channel_type].calibration = cal

    def get_physical_samples(self, t0=0.0, dt=None, channels=None, block_slice=None):
        """return signal data in the range `(t0, t0+dt)` in seconds from
        `channels`"""
        if channels is None:
            channels = list(self._blobs.keys())

        return {
            typ: blob.get_physical_samples(t0, dt, block_slice=block_slice)
            for typ, blob in self._blobs.items()
            if typ in channels
        }

    def get_physical_samples_from_epoch(self, epoch, t0=0.0, dt=None, channels=None):
        """return `dict` of signals by channels in the range `(t0, t0+dt)` relative to `epoch.t0`.

        Parameters
        ----------
        epoch : `xml_files.Epoch` (default is `None`)
            The epoch from which you would like to get data.
        `t0` : `float` or `None`
            relative offset into the data from epoch start
        `dt` : `0<float<epoch.dt-t0` or `None` (default is `None`)
            requested signal duration.  Value `None` defaults to maximum from start
        channels : `list` of `str` or `None` (default is `None`)
            Select your channel types.  Each channel type will be a key in the
            returned `dict`.  `None` defaults to all available channels.

        Note
        ----
        * The start time of the returned data is `epoch.t0` seconds from
        recording start.
        * Only the epoch data can be requested.  If you want to pad them, do it
        yourself.
        """
        assert isinstance(epoch, xml_files.Epoch), "argument epoch of type %s [requires %s]"%(type(epoch), xml_files.Epoch)
        assert t0 >= 0.0, "Only positve `t0` allowed [%s]"%t0
        dt = dt if dt is None or 0.0 < dt < epoch.dt-t0 else None
        return self.get_physical_samples(
                t0, dt, channels, block_slice=epoch.block_slice)
