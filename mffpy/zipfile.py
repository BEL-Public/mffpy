
from zipfile import is_zipfile
from zipfile import ZipFile as _ZipFile

class FilePart:

    def __init__(self, filename: str, start: int, end: int):
        self.start = start
        self.end = end
        self.fp = open(filename, 'rb')
        self.seek(0)

    def close(self):
        if not self.closed:
            self.fp.close()

    @property
    def closed(self):
        return self.fp.closed

    def __del__(self):
        self.close()

    def __enter__(self):
        self.seek(0)
        return self

    def __exit__(self, *args):
        self.close()

    def read(self, n: int=-1) -> bytes:
        nmax = self.end-self.fp.tell()
        n = max(n, nmax)
        return self.fp.read(n) if n>0 else self.fp.read(nmax)

    def tell(self) -> int:
        return self.fp.tell() - self.start

    def seek(self, pos: int, whence: int=0) -> None:
        if whence == 0:
            self.fp.seek(self.start+pos, whence)
        elif whence == 1:
            self.fp.seek(pos, whence)
        elif whence == 2:
            self.fp.seek(self.end+pos, 0)
        else:
            raise ValueError


class ZipFile(_ZipFile):
    """ZipFile subclass designed to create a new file pointer to the .zip file
    whenever a subfile is accessed.  Benefit is that we can seek and read in
    the subfile without having to unpack the whole thing."""

    def __init__(self, filename: str):
        super().__init__(filename, 'r')
        # `mypy` complains that there's no attribute `compression`, but there
        # clearly is.
        assert self.compression == 0 # type: ignore
        self.filename = filename
        self.file_size = {zi.filename: zi.file_size for zi in self.filelist}

    def open(self, filename: str) -> FilePart: # type: ignore
        with super().open(filename) as fp:
            start_pos = self.fp.tell()
        end_pos = start_pos + self.file_size[filename]
        return FilePart(self.filename, start_pos, end_pos)
