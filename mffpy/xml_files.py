"""Parsing for all xml files"""

import re
import logging
import xml.etree.ElementTree as ET
from os.path import basename, splitext
from datetime import datetime
from collections import namedtuple

import numpy as np
from typing import Tuple, Dict, List, Any, Union, IO

from cached_property import cached_property

from .json2xml import TEXT, ATTR
from .epoch import Epoch

FilePointer = Union[str, IO[bytes]]

class XMLType(type):
    """`XMLType` registers all xml types
    
    Spawn the _right_ XMLType sub-class with `from_file`.  To be registered,
    sub-classes need to implement class attributes `_xmlns` and
    `_xmlroottag`."""

    _registry: Dict[str, Any] = {}
    _tag_registry: Dict[str, Any] = {}
    _logger = logging.getLogger(name='XMLType')
    _extensions = ['.xml', '.XML']
    _supported_versions: Tuple[str, ...] = ('',)
    _time_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    def __new__(typ, name, bases, dct):
        new_xml_type = super().__new__(typ, name, bases, dct)
        typ.register(new_xml_type)
        return new_xml_type

    @classmethod
    def register(typ, xml_type):
        try:
            ns_tag = xml_type._xmlns + xml_type._xmlroottag
            if ns_tag in typ._registry:
                typ._logger.warn("overwritting %s in registry"%typ._registry[ns_tag])
            typ._registry[ns_tag] = xml_type
            # add another key for the same type
            typ._tag_registry[xml_type._xmlroottag] = xml_type
            return True
        except (AttributeError, TypeError):
            typ._logger.info("type %s cannot be registered"%xml_type)
            return False

    @classmethod
    def from_file(typ, filepointer: FilePointer):
        """return new `XMLType` instance of the appropriate sub-class

        **Parameters**
        *filepointer*: str or IO[bytes]
            pointer to the xml file
        """
        xml_root = ET.parse(filepointer).getroot()
        return typ._registry[xml_root.tag](xml_root)

    @classmethod
    def todict(typ, xmltype, **kwargs) -> Dict[str, Any]:
        """return dict of `kwargs` specific for `xmltype`

        The output of this function is supposed to fit perfectly into
        `mffpy.json2xml.dict2xml` returning a valid .xml file for the specific
        xml type.  For this, each of these types needs to implement a method
        `content` that takes `**kwargs` as argument.
        """
        assert xmltype in typ._tag_registry, f"""
        {xmltype} is not one of the valid .xml types:
        {typ._tag_registry.keys()}"""
        T = typ._tag_registry[xmltype]
        return {
            'content': T.content(**kwargs),
            'rootname': T._xmlroottag,
            'filename': T._default_filename,
            # remove the '}'/'{' characters
            'namespace': T._xmlns[1:-1]
        }


class XML(metaclass=XMLType):

    _default_filename: str = ''

    def __init__(self, xml_root):
        self.root = xml_root

    @classmethod
    def _parse_time_str(cls, txt):
        # convert time string "2003-04-17T13:35:22.000000-08:00"
        # to "2003-04-17T13:35:22.000000-0800" ..
        if txt.count(':') == 3:
            txt = txt[::-1].replace(':', '', 1)[::-1] 
        return datetime.strptime(txt, cls._time_format)

    @classmethod
    def _dump_datetime(cls, dt):
        txt = dt.strftime(cls._time_format)
        return txt[:-2] + ':' + txt[-2:]

    def find(self, tag, root=None):
        root = root or self.root
        return root.find(self._xmlns+tag)

    def findall(self, tag, root=None):
        root = root or self.root
        return root.findall(self._xmlns+tag)

    def nsstrip(self, tag):
        return tag[len(self._xmlns):]

    @classmethod
    def content(typ, *args, **kwargs):
        """checks and returns `**kwargs` as a formatted dict"""
        raise NotImplementedError(f"""
        json converter not implemented for type {typ}""")



class FileInfo(XML):

    _xmlns = '{http://www.egi.com/info_mff}'
    _xmlroottag = 'fileInfo'
    _default_filename = 'info.xml'
    _supported_versions = ('3',)
    
    @cached_property
    def version(self):
        el = self.find('mffVersion')
        return None if el is None else el.text

    @cached_property
    def recordTime(self):
        el = self.find('recordTime')
        return self._parse_time_str(el.text) if el is not None else None

    @classmethod
    def content(cls, recordTime: datetime, mffVersion: str = '3') -> dict: # type: ignore
        """returns mffVersion and time of recording start

        As version we only provide '3' at this time.  The time has to provided
        as a `datetime.datetime` object."""
        mffVersion = str(mffVersion)
        assert mffVersion in cls._supported_versions, f"""
        version {mffVersion} not supported"""
        return {
            'mffVersion': {
                TEXT: mffVersion
            },
            'recordTime': {
                TEXT: cls._dump_datetime(recordTime)
            }
        }


class DataInfo(XML):

    _xmlns = r'{http://www.egi.com/info_n_mff}'
    _xmlroottag = r'dataInfo'
    _default_filename = 'info1.xml'

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


class Patient(XML):

    _xmlns = r'{http://www.egi.com/subject_mff}'
    _xmlroottag = r'patient'
    _default_filename = 'subject.xml'

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

    @classmethod
    def content(self, name, data, dataType='string'):
        return {
            'fields': {
                'field': [
                    {
                        TEXT: {
                            'name': {TEXT: name},
                            'data': {TEXT: data,
                                ATTR: {'dataType': dataType}}
                        }
                    }
                ]
            }
        }


class SensorLayout(XML):

    _xmlns = r'{http://www.egi.com/sensorLayout_mff}'
    _xmlroottag = r'sensorLayout'
    _default_filename = 'sensorLayout.xml'

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
        assert self.nsstrip(el.tag) == 'sensor', f"""
        Unknown sensor with tag '{self.nsstrip(el.tag)}'"""
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


class Coordinates(XML):

    _xmlns = r'{http://www.egi.com/coordinates_mff}'
    _xmlroottag = r'coordinates'
    _default_filename = 'coordinates.xml'
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


class Epochs(XML):

    _xmlns = r'{http://www.egi.com/epochs_mff}'
    _xmlroottag = r'epochs'
    _default_filename = 'epochs.xml'
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
            for epoch in self.root
        ]

    def _parse_epoch(self, el):
        assert self.nsstrip(el.tag) == 'epoch', "Unknown epoch with tag '%s'"%self.nsstrip(el.tag)

        def elem2KeyVal(e):
            key = self.nsstrip(e.tag)
            val = self._type_converter[key](e.text)
            return key, val

        return Epoch(**{key: val
            for key, val in map(elem2KeyVal, el)})

    @classmethod
    def content(cls, epochs: List[Epoch]) -> dict: # type: ignore
        return {
            'epoch': [
                epoch.content
                for epoch in epochs
            ]
        }


class EventTrack(XML):

    _xmlns = r'{http://www.egi.com/event_mff}'
    _xmlroottag = r'eventTrack'
    _default_filename = 'Events.xml'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_type_converter = {
            'beginTime': lambda e: self._parse_time_str(e.text),
            'duration': lambda e: int(e.text),
            'relativeBeginTime': lambda e: int(e.text),
            'segmentationEvent': lambda e: e.text == 'true',
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


class Categories(XML):
    """Parser for 'categories.xml' file
    
    These files have the following structure:
    ```
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <categories xmlns="http://www.egi.com/categories_mff" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <cat>
            <name>ULRN</name>
            <segments>
                <seg status="bad">
                    <faults>
                        <fault>eyeb</fault>
                        <fault>eyem</fault>
                        <fault>badc</fault>
                    </faults>
                    <beginTime>0</beginTime>
                    <endTime>1200000</endTime>
                    <evtBegin>201981</evtBegin>
                    <evtEnd>201981</evtEnd>
                    <channelStatus>
                        <channels signalBin="1" exclusion="badChannels">1 12 15 50 251 253</channels>
                    </channelStatus>
                    <keys />
                </seg>
                ...
    ```
    """

    _xmlns = r'{http://www.egi.com/categories_mff}'
    _xmlroottag = r'categories'
    _default_filename = 'categories.xml'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._segment_converter = {
            'beginTime': lambda e: int(e.text),
            'endTime': lambda e: int(e.text),
            'evtBegin': lambda e: int(e.text),
            'evtEnd': lambda e: int(e.text),
            'channelStatus': self._parse_channel_status,
            'keys': lambda e: None,
            'faults': self._parse_faults,
        }
        self._channel_prop_converter = {
            'signalBin': int,
            'exclusion': str,
        }

    @cached_property
    def categories(self):
        return dict(self._parse_cat(cat) for cat in self.findall('cat'))

    def __getitem__(self, k):
        return self.categories[k]

    def __contains__(self, k):
        return k in self.categories

    def __len__(self):
        return len(self.categories)

    def _parse_cat(self, cat_el) -> Tuple[str, List[Dict[str, Any]]]:
        """parse element <cat>
        
        Contains <name /> and a <segments /> 
        """
        assert self.nsstrip(cat_el.tag) == 'cat', "Unknown cat with tag '%s'"%self.nsstrip(cat_el.tag)
        name = self.find('name', cat_el).text
        segment_els = self.findall('seg', self.find('segments', cat_el))
        segments = [self._parse_segment(seg_el) for seg_el in segment_els]
        return name, segments

    def _parse_channel_status(self, status_el):
        """parse element <channelStatus>
        
        Contains <channels />
        """
        ret = []
        for channel_el in self.findall('channels', status_el):
            channel = {
                prop: converter(channel_el.get(prop))
                for prop, converter in self._channel_prop_converter.items()
            }
            indices = map(int, channel_el.text.split() if channel_el.text else [])
            channel['channels'] = list(indices)
            ret.append(channel)
        return ret

    def _parse_faults(self, faults_el):
        """parse element <faults>
        
        Contains a bunch of <fault />"""
        return [el.text for el in self.findall('fault', faults_el)]

    def _parse_segment(self, seg_el):
        """parse element <seg>
        
        Contains several elements <faults/>, <beginTime/> etc."""
        ret = {'status': seg_el.get('status', None)}
        for el_key, converter in self._segment_converter.items():
            ret[el_key] = converter(self.find(el_key, seg_el))
        return ret
