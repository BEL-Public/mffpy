
from collections import namedtuple

from .dict2xml import TEXT

class Epoch:
    """class describing a recording epoch

    .mff files can be discontinuous.  Each part is described by one `Epoch`
    instance with properties `Epoch.t0`, `Epoch.dt`, and for convenience
    `Epoch.t1`.
    """

    _s_per_us = 10**-6

    def __init__(self, beginTime, endTime, firstBlock, lastBlock):
        self.beginTime = beginTime
        self.endTime = endTime
        self.firstBlock = firstBlock
        self.lastBlock = lastBlock

    def add_block(self, duration):
        self.lastBlock += 1
        self.endTime += duration

    @property
    def t0(self):
        """return start time of the epoch in seconds"""
        return self.beginTime*self._s_per_us

    @property
    def t1(self):
        """return end time of the epoch in seconds"""
        return self.t0+self.dt

    @property
    def dt(self):
        """return duration of the epoch in seconds"""
        return (self.endTime-self.beginTime)*self._s_per_us

    @property
    def block_slice(self):
        """return slice to access data blocks containing the epoch"""
        return slice(self.firstBlock-1, self.lastBlock)

    def __str__(self):
        return f"""Epoch:
        t0 = {self.t0} sec.; dt = {self.dt} sec.
        Data in blocks {self.block_slice}"""

    @property
    def content(self):
        return {
            TEXT: {
                'beginTime': {TEXT: str(self.beginTime)},
                'endTime': {TEXT: str(self.endTime)},
                'firstBlock': {TEXT: str(self.firstBlock)},
                'lastBlock': {TEXT: str(self.lastBlock)}
            }
        }
