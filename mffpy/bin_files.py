
import numpy as np
from . import raw_bin_files
from . import xml_files

class BinFile(raw_bin_files.RawBinFile):

    _raw_unit = 'uV'
    _unit = _raw_unit
    _scale = 1.0
    _scale_converter = {
        'VV': 1.0,
        'mVmV': 1.0,
        'uVuV': 1.0,
        'VmV': 1.0*10**3,
        'mVV': 1.0*10**-3,
        'VuV': 1.0*10**6,
        'uVV': 1.0*10**-6,
        'mVuV': 1.0*10**3,
        'uVmV': 1.0*10**-3,
    }

    def __init__(self, bin_filename, info_filename=None, signal_type='EEG'):
        super().__init__(bin_filename)
        self.info_filename = info_filename
        self.signal_type = signal_type
        self.calibration = None

    @property
    def info_filename(self):
        return self._info.filename

    @info_filename.setter
    def info_filename(self, fn):
        self._info = xml_files.open(fn) if fn else None
        assert fn is None or isinstance(self._info, xml_files.DataInfo), 'Wrong xml info file ["%s"]'%fn

    @property
    def calibrations(self):
        return self._info.calibrations

    @property
    def calibration(self, ctype='GCAL'):
        return self._calibration

    @calibration.setter
    def calibration(self, cal):
        self._calibration = np.ones(self.num_channels, dtype=np.float64)[:, None]
        if cal is not None:
            assert cal in self.calibrations, "Request calibration '%s' is not available.  Choose one of %s"%(cal, list(self.calibrations.keys()))
            calibration = self.calibrations[cal]
            assert calibration['beginTime'] == 0, 'Calibration "%s" begins not at recording start'%cal
            for i, c in calibration['channels'].items():
                self._calibration[i-1] = c

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, u):
        self._scale = self._scale_converter[self._raw_unit+u]
        self._unit = u

    @property
    def scale(self):
        return self._scale

    def get_physical_samples(self, t0=0.0, dt=None, dtype=np.float32):
        return (self.calibration*self.scale*self.read_raw_samples(t0, dt)).astype(dtype)
