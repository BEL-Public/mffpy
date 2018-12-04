"""Parsing for all xml files"""

import re
import xml.etree.ElementTree as ET
import base64
import numpy as np
from os.path import basename, splitext
from datetime import datetime
from collections import namedtuple
from .cached_property import cached_property

_datainfo_re = re.compile("info")
_eventtrack_re = re.compile("Events")

def open(filename):

    _xml_by_name = {
        'coordinates': Coordinates,
        'epochs': Epochs,
        'info': FileInfo,
        'sensorLayout': SensorLayout,
        'subject': Patient
    }

    name = splitext(basename(filename))[0]
    if name in _xml_by_name:
        return _xml_by_name[name](filename)
    elif _datainfo_re.match(name):
        return DataInfo(filename)
    elif _eventtrack_re.match(name):
        return EventTrack(filename)
    else:
        raise ValueError("Unknown xml file: %s"%filename)


class XMLBase:

    _extensions = ['.xml', '.XML']
    _ext_err = "Unknown file type ['%s']"
    _xmlns = None
    _xmlroottag = None
    _supported_versions = (None,)
    _time_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    @classmethod
    def _parse_time_str(cls, txt):
        # convert time string "2003-04-17T13:35:22.000000-08:00"
        # to "2003-04-17T13:35:22.000000-0800" ..
        assert txt.count(':') == 3, "unexpected time string '%s'"%txt
        txt = txt[::-1].replace(':', '', 1)[::-1] 
        return datetime.strptime(txt, cls._time_format)

    def __init__(self, filename):
        self.filename = filename
        self._check_ext()

    def _check_ext(self):
        assert splitext(self.filename)[1] in self._extensions, self._ext_err%self.filename

    @cached_property
    def _xml_root(self):
        __xml_root = ET.parse(self.filename).getroot()
        assert __xml_root.tag == self._xmlns+self._xmlroottag, "XML format in file '%s': root tag '%s' ['%s']."%(self.filename, __xml_root.tag, self._xmlns+self._xmlroottag)
        return __xml_root

    def find(self, tag, root=None):
        root = root or self._xml_root
        return root.find(self._xmlns+tag)

    def findall(self, tag, root=None):
        root = root or self._xml_root
        return root.findall(self._xmlns+tag)

    def nsstrip(self, tag):
        return tag[len(self._xmlns):]


class FileInfo(XMLBase):

    _xmlns = '{http://www.egi.com/info_mff}'
    _xmlroottag = 'fileInfo'
    _supported_versions = ('3',)
    
    @cached_property
    def version(self):
        el = self.find('mffVersion')
        return None if el is None else el.text

    @cached_property
    def recordTime(self):
        el = self.find('recordTime')
        return self._parse_time_str(el.text) if el is not None else None


class DataInfo(XMLBase):

    _xmlns = r'{http://www.egi.com/info_n_mff}'
    _xmlroottag = r'dataInfo'

    @cached_property
    def generalInformation(self):
        el = self.find('fileDataType', self.find('generalInformation'))
        el = el[0]
        info = {}
        info['channel_type'] = self.nsstrip(el.tag)
        for el_i in el:
            info[self.nsstrip(el_i.tag)] = el_i.text
        return info

    @cached_property
    def filters(self):
        return [
            self._parse_filter(f)
            for f in self.find('filters')
        ]
    
    def _parse_filter(self, f):
        ans = {}
        for prop in (('beginTime', float), 'method', 'type'):
            prop, conv = prop if len(prop) == 2 else (prop, lambda x: x)
            ans[prop] = conv(self.find(prop, f).text)

        el = self.find('cutoffFrequency', f)
        ans['cutoffFrequency'] = (float(el.text), el.get('units'))
        return ans

    @cached_property
    def calibrations(self):
        calibrations = self.find('calibrations')
        ans = {}
        for cali in calibrations:
            typ = self.find('type', cali)
            ans[typ.text] = self._parse_calibration(cali) 
        return ans

    def _parse_calibration(self, cali):
        ans = {}
        ans['beginTime'] = float(self.find('beginTime', cali).text)
        ans['channels'] = {
            int(el.get('n')): np.float32(el.text)
            for el in self.find('channels', cali)
        }
        return ans


class Patient(XMLBase):

    _xmlns = r'{http://www.egi.com/subject_mff}'
    _xmlroottag = r'patient'

    _type_converter = {
        'string': str,
        None: lambda x: x
    }

    @cached_property
    def fields(self):
        ans = {}
        for field in self.find('fields'):
            assert self.nsstrip(field.tag) == 'field', "Unknown field with tag '%s'"%self.nsstrip(field.tag)
            name = self.find('name', field).text
            data = self.find('data', field)
            data = self._type_converter[data.get('dataType')](data.text)
            ans[name] = data
        return ans


class SensorLayout(XMLBase):

    _xmlns = r'{http://www.egi.com/sensorLayout_mff}'
    _xmlroottag = r'sensorLayout'

    _type_converter = {
        'name': str,
        'number': int,
        'type': int,
        'identifier': int,
        'x': np.float32,
        'y': np.float32,
        'z': np.float32,
    }

    @cached_property
    def name(self):
        el = self.get('name')
        return 'UNK' if el is None else el.text

    @cached_property
    def sensors(self):
        return dict([
            self._parse_sensor(sensor)
            for sensor in self.find('sensors')
        ])

    def _parse_sensor(self, el):
        assert self.nsstrip(el.tag) == 'sensor', "Unknown sensor with tag '%s'"%self.nsstrip(el.tag)
        ans = {}
        for e in el:
            tag = self.nsstrip(e.tag)
            ans[tag] = self._type_converter[tag](e.text)
        return ans['number'], ans

    @cached_property
    def threads(self):
        ans = []
        for thread in self.find('threads'):
            assert self.nsstrip(thread.tag) == 'thread', "Unknown thread with tag '%s'"%self.nsstrip(thread.tag)
            ans.append(tuple(map(int, thread.text.split(','))))
        return ans

    @cached_property
    def tilingSets(self):
        ans = []
        for tilingSet in self.find('tilingSets'):
            assert self.nsstrip(tilingSet.tag) == 'tilingSet', "Unknown tilingSet with tag '%s'"%self.nsstrip(tilingSet.tag)
            ans.append(list(map(int, tilingSet.text.split())))
        return ans

    @cached_property
    def neighbors(self):
        ans = {}
        for ch in self.find('neighbors'):
            assert self.nsstrip(ch.tag) == 'ch', "Unknown ch with tag '%s'"%self.nsstrip(ch.tag)
            key = int(ch.get('n'))
            ans[key] = list(map(int, ch.text.split()))
        return ans

    @property
    def mappings(self):
        raise NotImplementedError("No method to parse mappings.")


class Coordinates(XMLBase):

    _xmlns = r'{http://www.egi.com/coordinates_mff}'
    _xmlroottag = r'coordinates'
    _type_converter = {
        'name': str,
        'number': int,
        'type': int,
        'identifier': int,
        'x': np.float32,
        'y': np.float32,
        'z': np.float32,
    }

    @cached_property
    def acqTime(self):
        txt = self.find("acqTime").text
        return self._parse_time_str(txt)

    @cached_property
    def acqMethod(self):
        el = self.find("acqMethod")
        return el.text

    @cached_property
    def name(self):
        el = self.get('name')
        return 'UNK' if el is None else el.text

    @cached_property
    def defaultSubject(self):
        return bool(self.find('defaultSubject').text)

    @cached_property
    def sensors(self):
        sensorLayout = self.find('sensorLayout')
        return dict([
            self._parse_sensor(sensor)
            for sensor in self.find('sensors', sensorLayout)
        ])

    def _parse_sensor(self, el):
        assert self.nsstrip(el.tag) == 'sensor', "Unknown sensor with tag '%s'"%self.nsstrip(el.tag)
        ans = {}
        for e in el:
            tag = self.nsstrip(e.tag)
            ans[tag] = self._type_converter[tag](e.text)
        return ans['number'], ans


_Epoch = namedtuple("Epoch", "beginTime endTime firstBlock lastBlock")
class Epoch(_Epoch):
    """class describing a recording epoch

    .mff files can be discontinuous.  Each part is described
    by one `Epoch` instance with properties `Epoch.t0`, `Epoch.dt`,
    and for convenience `Epoch.t1`.
    """

    _s_per_us = 10**-6

    @property
    def t0(self):
        """
        ```python
        Epoch.t0
        ```
        return start time of the epoch in seconds
        """
        return self.beginTime*self._s_per_us

    @property
    def t1(self):
        """
        ```python
        Epoch.t1
        ```
        return end time of the epoch in seconds
        """
        return self.t0+self.dt

    @property
    def dt(self):
        """
        ```python
        Epoch.dt
        ```
        return duration of the epoch in seconds
        """
        return (self.endTime-self.beginTime)*self._s_per_us

    @property
    def block_slice(self):
        """return slice to access data blocks containing the epoch"""
        return slice(self.firstBlock-1, self.lastBlock)

    def __str__(self):
        s = 'Epoch:\n'
        s+= '\tt0 = %s sec.;\tdt = %s sec.\n'%(self.t0, self.dt)
        s+= '\tData in blocks %s\n'%self.block_slice
        return s


class Epochs(XMLBase):

    _xmlns = r'{http://www.egi.com/epochs_mff}'
    _xmlroottag = r'epochs'
    _type_converter = {
        'beginTime': int,
        'endTime': int,
        'firstBlock': int,
        'lastBlock': int,
    }

    def __getitem__(self, n):
        return self.epochs[n]

    @cached_property
    def epochs(self):
        return [
            self._parse_epoch(epoch)
            for epoch in self._xml_root
        ]

    def _parse_epoch(self, el):
        assert self.nsstrip(el.tag) == 'epoch', "Unknown epoch with tag '%s'"%self.nsstrip(el.tag)

        def elem2KeyVal(e):
            key = self.nsstrip(e.tag)
            val = self._type_converter[key](e.text)
            return key, val

        return Epoch(**{key: val
            for key, val in map(elem2KeyVal, el)})


class EventTrack(XMLBase):

    _xmlns = r'{http://www.egi.com/event_mff}'
    _xmlroottag = r'eventTrack'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_type_converter = {
            'beginTime': lambda e: self._parse_time_str(e.text),
            'duration': lambda e: int(e.text),
            'code': lambda e: str(e.text),
            'label': lambda e: str(e.text),
            'description': lambda e: str(e.text),
            'sourceDevice': lambda e: str(e.text),
            'keys': self._parse_keys
        }
        self._key_type_converter = {
            'short': np.int16,
            'string': str,
        }

    @cached_property
    def name(self):
        return self.find('name').text

    @cached_property
    def trackType(self):
        return self.find('trackType').text

    @cached_property
    def events(self):
        return [
            self._parse_event(event)
            for event in self.findall('event')
        ]

    def _parse_event(self, events_el):
        assert self.nsstrip(events_el.tag) == 'event', "Unknown event with tag '%s'"%self.nsstrip(events_el.tag)
        return {
            tag: self._event_type_converter[tag](el)
            for tag, el in map(lambda e: (self.nsstrip(e.tag), e), events_el)
        }

    def _parse_keys(self, keys_el):
        return dict([self._parse_key(key_el)
            for key_el in keys_el])

    def _parse_key(self, key):
        """
        Attributes :
            key (ElementTree.XMLElement) : parsed from a structure 
                ```
                <key>
                    <keyCode>cel#</keyCode>
                    <data dataType="short">1</data>
                </key>
                ```
        """
        code = self.find('keyCode', key).text
        data = self.find('data', key)
        val = self._key_type_converter[data.get('dataType')](data.text)
        return code, val 
