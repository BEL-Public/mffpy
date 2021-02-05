"""Management of optional header blocks in .mff binary files

**Optional header block structure**

1. `class NoOptHeaderBlock`

+------------+----------+----------------------------+
| start byte | end byte |        description         |
+------------+----------+----------------------------+
|          0 |        4 | additional byte length = 0 |
+------------+----------+----------------------------+

2. `class Type1Block`

+------------+----------+-----------------------------+
| start byte | end byte |         description         |
+------------+----------+-----------------------------+
|          0 |        4 | additional byte length = 24 |
|          4 |       12 | total number of blocks      |
|         12 |       20 | total number of samples     |
|         20 |       24 | total number of signals     |
+------------+----------+-----------------------------+
"""
from typing import Union, Dict, Type
from collections import namedtuple

from .helpers import FileLike, read, write


_NoOptHeaderBlock = namedtuple('_NoOptHeaderBlock', '')


class NoOptHeaderBlock(_NoOptHeaderBlock):
    byte_size = 0

    @classmethod
    def from_file(cls, fp: FileLike):
        """create new empty header block"""
        return cls()

    def write(self, fp: FileLike):
        """write empty header block to file"""
        write(fp, 'i', (0,))


_Type1Block = namedtuple(
    '_Type1Block',
    'total_num_blocks total_num_samples total_num_signals'
)


class Type1Block(_Type1Block):
    byte_size = 24
    bytes_format = '2qi'

    @classmethod
    def from_file(cls, fp: FileLike):
        """create type-1 header block from file"""
        args = read(fp, cls.bytes_format)
        return cls(*args)

    def write(self, fp: FileLike):
        """write type-1 header block to file"""
        bytes_format = '2i' + self.bytes_format
        content = (self.byte_size, 1) + self
        write(fp, bytes_format, content)


BlockConstructors = Union[Type[NoOptHeaderBlock], Type[Type1Block]]
BlockTypes = Union[NoOptHeaderBlock, Type1Block]

block_by_type: Dict[int, BlockConstructors] = {
    0: NoOptHeaderBlock,
    1: Type1Block
}


def from_file(fp: FileLike):
    """return infered header block read from file"""
    byte_size = read(fp, 'i')
    typ = read(fp, 'i') if byte_size else 0
    if typ not in block_by_type:
        raise ValueError(f"Invalid optional header with type {typ}")

    return block_by_type[typ].from_file(fp)
