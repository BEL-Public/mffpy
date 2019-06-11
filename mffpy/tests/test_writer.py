
from datetime import datetime
import pytest
from os import makedirs, rmdir, remove
from os.path import join
from ..writer import Writer
from ..reader import Reader
from ..xml_files import XML

def test_writer_doesnt_overwrite():
    dirname = 'testdir.mff'
    makedirs(dirname)
    with pytest.raises(AssertionError):
        W = Writer(dirname)
    rmdir(dirname)

def test_writer_writes():
    dirname = 'testdir2.mff'
    W = Writer(dirname)
    startdatetime = datetime.strptime('1984-02-18T14:00:10.000000+0100', XML._time_format)
    # write the file info; read it again; compare the result
    W.add('fileInfo', recordTime=startdatetime)
    W.write()
    R = Reader(dirname)
    assert R.startdatetime == startdatetime
    # cleanup
    remove(join(dirname, 'info.xml'))
    rmdir(dirname)
