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
from typing import Tuple, Dict, IO

import numpy as np

from . import raw_bin_files
from .xml_files import DataInfo


class BinFile(raw_bin_files.RawBinFile):

    _raw_unit: str = 'uV'
    _unit: str = _raw_unit
    _scale: float = 1.0
    _scale_converter: Dict[str, float] = {
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

    def __init__(self, bin_file: IO[bytes], info: DataInfo,
                 signal_type: str = 'EEG'):
        super().__init__(bin_file)
        self._info = info
        self.signal_type = signal_type
        self.calibration = 'GCAL' if 'GCAL' in \
            self.calibrations.keys() else None

    @property
    def calibrations(self):
        return self._info.calibrations

    @property
    def calibration(self):
        return self._calibration

    @calibration.setter
    def calibration(self, cal: str):
        """If no calibrations in DataInfo file set
        self._calibration equal to an array of 1s
        with self.num_channel columns. Otherwise,
        load GCAL values into the array."""
        self._calibration = np.ones(
            self.num_channels, dtype=np.float64)[:, None]
        if cal is not None:
            assert cal in self.calibrations, f"""
            Request calibration '{cal}' is not available.  Choose one of:
            {list(self.calibrations.keys())}"""
            calibration = self.calibrations[cal]
            assert calibration['beginTime'] == 0, f"""
            Calibration "{cal}" begins not at recording start"""
            for i, c in calibration['channels'].items():
                self._calibration[i-1] = c

    @property
    def unit(self) -> str:
        return self._unit

    @unit.setter
    def unit(self, u: str):
        self._scale = self._scale_converter[self._raw_unit+u]
        self._unit = u

    @property
    def scale(self) -> float:
        return self._scale

    def get_physical_samples(self, t0: float = 0.0,
                             dt: float = None, block_slice: slice = None,
                             dtype=np.float32) -> Tuple[np.ndarray, float]:
        samples, start_time = self.read_raw_samples(
            t0, dt, block_slice=block_slice)
        return (self.calibration*self.scale*samples).astype(dtype), start_time
