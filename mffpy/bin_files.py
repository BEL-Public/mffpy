
from . import raw_bin_files

class BinFile(raw_bin_files.RawBinFile):

    def __init__(self, bin_filename, info_filename=None):
        super().__init__(bin_filename)

    @property
    def signal_type(self):
        return 'EEG'
