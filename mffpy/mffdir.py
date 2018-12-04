
import re
from os import listdir
from collections import defaultdict, namedtuple
from os.path import join, exists, splitext, basename
from .cached_property import cached_property

from . import xml_files

SignalAndInfo = namedtuple('SignalAndInfo', 'signal info')


class MFFDirectory(str):
    """.mff directory path

    An `MFFDirectory` string contains the path to a valid .mff directory.
    """

    _extensions = ('.mff',)
    _ext_err = 'Unknown file type ["%s"]'
    _re_nu = re.compile(r'\d+')

    def __init__(self, filename):
        """initialize new .mff directory instance

        **Parameters:**
        `filename` (str) - the full path to the .mff directory.
        """
        self._find_files_by_type()
        self._check()

    def _find_files_by_type(self):
        """Reads the directory and sorts filenames by extensions in property `files_by_type`
        """
        self.files_by_type = defaultdict(list)

        for fbase, ext in map(splitext, listdir(self)):
            self.files_by_type[ext].append(fbase)

    def filename(self, basename):
        for ext, files in self.files_by_type.items():
            if basename in files:
                return join(self, basename) + ext
        else:
            raise ValueError('No file with basename "%s" in directory "%s".'%(basename, super().__str__()))

    def info(self, i=None):
        """returns filename `<self>/file.xml` if `i is None`, otherwise `<self>/file<i>.xml`
        """
        return self.filename('info'+(str(i) if i else ''))

    def signals_with_info(self):
        ans = []
        for signalfile in self.files_by_type['.bin']:
            bin_num = self._re_nu.search(basename(signalfile)).group()
            ans.append(SignalAndInfo(
                signal = self.filename(signalfile),
                info = self.info(bin_num)
            ))
        return ans

    @cached_property
    def epochs(self):
        """
        ```python
        Epochs.epochs
        ```

        Return list of epochs.  Each epoch is of class `Epoch`.
        """
        return xml_files.open(self.filename('epochs'))

    def _check(self):
        """Checks the .mff directory for completeness
        """
        # MFF directory should have the right extension
        assert splitext(self)[1] in self._extensions, self._ext_err%super().__str__()
        # For each `signal%i.bin`, there should be an `info%i.xml`
        for signalfile in self.files_by_type['.bin']:
            assert 'signal' in signalfile, 'Unknown file "%s"'%signalfile
            bin_num = self._re_nu.search(signalfile).group()
            assert exists(self.info(bin_num)), 'No info found [%s]'%self.info(bin_num)

    def __str__(self):
        ans = "---\n"
        ans += '# .mff directory "%s/"\n'%super().__str__()
        ans += "---\n"
        ans += '## List of files\n'
        for ext, files in self.files_by_type.items():
            ans += "\n### Files of type %s\n\n"%ext
            for filename in files:
                ans += "  * %s\n"%(filename+ext)
        ans += "---"
        return ans
