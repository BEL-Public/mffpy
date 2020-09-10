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
from .dict2xml import TEXT


class Epoch:
    """class describing a recording epoch

    .mff files can be discontinuous.  Each part is described by one `Epoch`
    instance with properties `Epoch.t0`, `Epoch.dt`, and for convenience
    the end time `Epoch.t1` of the epoch.
    """

    _s_per_us = 10**-6
    name = 'epoch'

    def __init__(self, beginTime, endTime, firstBlock,
                 lastBlock):
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
        Name = {self.name}
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
