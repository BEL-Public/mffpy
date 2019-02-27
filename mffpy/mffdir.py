
import re
from os import listdir
from os.path import join, exists, splitext, basename, isdir
from io import BytesIO
from collections import defaultdict, namedtuple
from typing import Dict, List, Tuple, Any, Union, IO

from cached_property import cached_property

from . import xml_files
from .xml_files import XML
from . import zipfile


SignalAndInfo: Tuple[IO[bytes], str] = namedtuple('SignalAndInfo', 'signal info')


class MFFDirBase:
    """.mff directory path

    An `MFFDirBase` is able to access and spawn all file in an mff directory container.
    """

    _extensions: Tuple[str, ...] = ('.mff',)
    _ext_err = 'Unknown file type ["%s"]'
    _re_nu = re.compile(r'\d+')

    def __init__(self, filename: str):
        """initialize new .mff directory instance

        **Parameters:**
        `filename` (str) - the full path to the .mff directory.
        """
        self._mffname = filename
        self._find_files_by_type()
        self._check()

    def listdir(self) -> List[str]:
        raise NotImplementedError

    def __contains__(self, filename: str) -> bool:
        raise NotImplementedError

    def filepointer(self, basename: str) -> IO[bytes]:
        raise NotImplementedError

    def filename(self, basename: str) -> str:
        raise NotImplementedError

    def _find_files_by_type(self) -> None:
        """Reads the directory and sorts filenames by extensions in property `files_by_type`
        """
        self.files_by_type: Dict[str, List[str]] = defaultdict(list)
        for fbase, ext in (splitext(it) for it in self.listdir()):
            self.files_by_type[ext].append(fbase)

    def info(self, i: int=None) -> IO[bytes]:
        """returns filepointer `<self.filename>/file.xml` if `i is None`, otherwise `<self.filename>/file<i>.xml`
        """
        return self.filepointer('info'+(str(i) if i else ''))

    def signals_with_info(self) -> List[SignalAndInfo]:
        ans = []
        for signalfile in self.files_by_type['.bin']:
            matches = self._re_nu.search(basename(signalfile))
            assert matches is not None, "Something went wrong in '%s'"%signalfile
            bin_num = int(matches.group())
            ans.append(SignalAndInfo(
                signal = self.filepointer(signalfile),
                info = 'info%s'%bin_num
            ))
        return ans

    def _check(self) -> None:
        """Checks the .mff directory for completeness
        """
        # MFF directory should have the right extension
        assert splitext(self._mffname)[1] in self._extensions, self._ext_err%super().__str__()
        # For each `signal%i.bin`, there should be an `info%i.xml`
        for signalfile in self.files_by_type['.bin']:
            assert 'signal' in signalfile, 'Unknown file "%s"'%signalfile
            matches = self._re_nu.search(signalfile)
            assert matches is not None
            bin_num = int(matches.group())
            assert self.filename('info%s'%bin_num) in self, 'No info found [%s]'%self.info(bin_num)

    def __str__(self) -> str:
        ans = "---\n"
        ans += '# .mff directory "%s/"\n'%self._mffname
        ans += "---\n"
        ans += '## List of files\n'
        for ext, files in self.files_by_type.items():
            ans += "\n### Files of type %s\n\n"%ext
            for filename in files:
                ans += "  * %s\n"%(filename+ext)
        ans += "---"
        return ans


class MFFDirectory(MFFDirBase):
    """system-level .mff directory"""

    def listdir(self) -> List[str]:
        return listdir(self._mffname)

    def filepointer(self, basename: str) -> IO[bytes]:
        return open(self.filename(basename), 'rb')

    def filename(self, basename: str) -> str:
        for ext, files in self.files_by_type.items():
            if basename in files:
                return join(self._mffname, basename) + ext
        else:
            raise ValueError('No file with basename "%s" in directory "%s".'%(basename, super().__str__()))

    def __contains__(self, filename: str) -> bool:
        return exists(filename)


class ZippedMFFDirectory(MFFDirBase):
    """zipped .mff directory
    
    Note: Compression on the zip file has to be 0, i.e. `ZIP_STORE`.
    Create the zip file like
    ```bash
    $ zip -Z store -r -j zipped_example.mff ./example.mff
    ```
    """

    def __init__(self, filename: str):
        self.root = zipfile.ZipFile(filename)
        super().__init__(filename)

    def __del__(self):
        self.root.close()

    def listdir(self) -> List[str]:
        return self.root.namelist()

    def filepointer(self, basename: str) -> IO[bytes]:
        # type `FilePart` implements all methods necessary for `IO[bytes]`
        return self.root.open(self.filename(basename)) # type: ignore

    def filename(self, basename: str) -> str:
        for ext, files in self.files_by_type.items():
            if basename in files:
                return basename + ext
        else:
            raise ValueError('No file with basename "%s" in directory "%s".'%(basename, super().__str__()))

    def __contains__(self, filename: str) -> bool:
        return filename in self.listdir()


def get_directory(filename: str) -> MFFDirBase:
    """return either a system-level or a zipped .mff directory"""
    assert exists(filename), "'%s' does not exist"
    if isdir(filename):
        return MFFDirectory(filename)
    elif zipfile.is_zipfile(filename):
        return ZippedMFFDirectory(filename)
    else:
        raise ValueError("'%s' is likely a corrupted zip file"%filename)
