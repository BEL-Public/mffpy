import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from collections import defaultdict
import numpy as np
from typing import Tuple, Dict, List, Any, Union, IO
from .cached_property import cached_property
from .dict2xml import TEXT, ATTR
from .epoch import Epoch
import copy
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

"""Parsing for all xml files"""


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
                typ._logger.warn("overwritting %s in registry" %
                                 typ._registry[ns_tag])
            typ._registry[ns_tag] = xml_type
            # add another key for the same type
            typ._tag_registry[xml_type._xmlroottag] = xml_type
            return True
        except (AttributeError, TypeError):
            typ._logger.info("type %s cannot be registered" % xml_type)
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

    @classmethod
    def xml_root_tags(cls):
        """return list of root tags of supported xml files"""
        return list(cls._tag_registry.keys())


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
        assert dt.tzinfo is not None, f"""
        Timezone required for date/time {dt}"""
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

    @property
    def xml_root_tag(self):
        return self._xmlroottag

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
    def content(cls, recordTime: datetime,  # type: ignore
                mffVersion: str = '3') -> dict:
        """returns mffVersion and time of recording start

        As version we only provide '3' at this time.  The time has to provided
        as a `datetime.datetime` object.
        """

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

    def get_content(self):
        """return mff version and time of recording start"""
        return {
            'mffVersion': self.version,
            'recordTime': self.recordTime
        }

    def get_serializable_content(self):
        """return a serializable object containing the
        mff version and time of recording start"""
        content = copy.deepcopy(self.get_content())
        content['recordTime'] = XML._dump_datetime(content['recordTime'])
        return content


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
        filters = []
        if self.find('filters') is not None:
            filters = [self._parse_filter(f) for f in self.find('filters')]
        return filters

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
        if calibrations is not None:
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

    @classmethod
    def content(cls, fileDataType: str,  # type: ignore
                dataTypeProps: dict = None,
                filters: List[dict] = None,
                calibrations: List[dict] = None) -> dict:
        """returns info on the associated (data) .bin file

        **Parameters**

        *fileDataType*: indicates the type of data
        *dataTypeProps*: indicates the recording device
        *filters*: lists all applied filters
        *calibrations*: lists a number of calibrations
        """
        dataTypeProps = dataTypeProps or {}
        calibrations = calibrations or []
        filters = filters or []
        return {
            'generalInformation': {
                TEXT: {
                    'fileDataType': {
                        TEXT: {
                            fileDataType: {
                                TEXT: {
                                    k: {TEXT: v}
                                    for k, v in dataTypeProps.items()
                                }
                            }
                        }
                    }
                }
            },
            'filters': {
                'filter': [
                    {
                        'beginTime': {TEXT: f['beginTime']},
                        'method': {TEXT: f['method']},
                        'type': {TEXT: f['type']},
                        'cutoffFrequency': {TEXT: f['cutoffFrequency'],
                                            ATTR: {'units': 'Hz'}}
                    } for f in filters
                ]
            },
            'calibrations': {
                'calibration': [
                    {
                        'beginTime': {TEXT: cal['beginTime']},
                        'type': {TEXT: cal['type']},
                        'channels': {
                            'ch': [
                                {
                                    TEXT: str(v),
                                    ATTR: {'n': str(n)}
                                }
                            ] for k, (v, n) in cal.items()
                        }
                    } for cal in calibrations
                ]
            }
        }

    def get_content(self):
        """return info on the associated (data) .bin file"""
        return {
            'generalInformation': self.generalInformation,
            'filters': self.filters,
            'calibrations': self.calibrations
        }

    def get_serializable_content(self):
        """return a serializable object containing
        info on the associated (data) .bin file"""
        content = copy.deepcopy(self.get_content())
        # Convert np.float32 values to float built-in type
        for value in content['calibrations'].values():
            channels = value['channels']
            for channel in channels.keys():
                channels[channel] = float(channels[channel])
        return content


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
            assert self.nsstrip(field.tag) == 'field', f"""
            Unknown field with tag {self.nsstrip(field.tag)}"""
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

    def get_content(self):
        """return patient related info"""
        return {
            'fields': self.fields
        }

    def get_serializable_content(self):
        """return a serializable object
        containing patient related info"""
        return copy.deepcopy(self.get_content())


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
        'originalNumber': int
    }

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
    def name(self):
        el = self.find('name')
        return 'UNK' if el is None else el.text

    @cached_property
    def threads(self):
        ans = []
        if self.find('threads') is not None:
            for thread in self.find('threads'):
                assert self.nsstrip(thread.tag) == 'thread', f"""
                Unknown thread with tag {self.nsstrip(thread.tag)}"""
                ans.append(tuple(map(int, thread.text.split(','))))
        return ans

    @cached_property
    def tilingSets(self):
        ans = []
        if self.find('tilingSets') is not None:
            for tilingSet in self.find('tilingSets'):
                assert self.nsstrip(tilingSet.tag) == 'tilingSet', f"""
                Unknown tilingSet with tag {self.nsstrip(tilingSet.tag)}"""
                ans.append(list(map(int, tilingSet.text.split())))
        return ans

    @cached_property
    def neighbors(self):
        ans = {}
        if self.find('neighbors') is not None:
            for ch in self.find('neighbors'):
                assert self.nsstrip(ch.tag) == 'ch', f"""
                Unknown ch with tag {self.nsstrip(ch.tag)}"""
                key = int(ch.get('n'))
                ans[key] = list(map(int, ch.text.split()))
        return ans

    @property
    def mappings(self):
        raise NotImplementedError("No method to parse mappings.")

    def get_content(self):
        """return info on the sensor
        net used for the recording"""
        return {
            'name': self.name,
            'sensors': self.sensors,
            'threads': self.threads,
            'tilingSets': self.tilingSets,
            'neighbors': self.neighbors
        }

    def get_serializable_content(self):
        """return a serializable object containing
        info on the sensor net used for the recording"""
        content = copy.deepcopy(self.get_content())
        for field in ['sensors', 'neighbors']:
            # Stringify integer keys
            content[field] = {
                str(key): value
                for key, value in content[field].items()
            }
        # Convert np.float32 values to float built-in type
        for value in content['sensors'].values():
            for coord in ['x', 'y', 'z']:
                value[coord] = float(value[coord])
        # Convert list of tuples into a list of list
        content['threads'] = list(map(list, content['threads']))
        return content


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
        el = self.find('name', self.find('sensorLayout'))
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
        assert self.nsstrip(el.tag) == 'sensor', f"""
        Unknown sensor with tag {self.nsstrip(el.tag)}"""
        ans = {}
        for e in el:
            tag = self.nsstrip(e.tag)
            ans[tag] = self._type_converter[tag](e.text)
        return ans['number'], ans

    def get_content(self):
        """return info on the acquisition time and method,
        sensor net name and default subject"""
        return {
            'acqTime': self.acqTime,
            'acqMethod': self.acqMethod,
            'name': self.name,
            'defaultSubject': self.defaultSubject,
            'sensors': self.sensors
        }

    def get_serializable_content(self):
        """return a serializable object containing
        info on the acquisition time and method,
        sensor net name and default subject"""
        content = copy.deepcopy(self.get_content())
        content['acqTime'] = XML._dump_datetime(content['acqTime'])
        # Stringify integer keys
        content['sensors'] = {
            str(key): value
            for key, value in content['sensors'].items()
        }
        # Convert np.float32 values to float built-in type
        for value in content['sensors'].values():
            for coord in ['x', 'y', 'z']:
                value[coord] = float(value[coord])
        return content


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
        """If `n` is an int, interpret as index and return the
        corresponding epoch in the list. If `n` is a str, return
        a list of all epochs with name `n`, or the individual
        epoch if only one epoch with name `n`."""
        if isinstance(n, int):
            return self.epochs[n]
        elif isinstance(n, str):
            matched = list(filter(lambda epoch: epoch.name == n, self.epochs))
            return matched[0] if len(matched) == 1 else matched
        else:
            raise ValueError(f"Unsupported argument type '{n}': {type(n)}")

    def __len__(self):
        return len(self.epochs)

    @cached_property
    def epochs(self):
        return [
            self._parse_epoch(epoch)
            for epoch in self.root
        ]

    def _parse_epoch(self, el):
        assert self.nsstrip(el.tag) == 'epoch', f"""
        Unknown epoch with tag {self.nsstrip(el.tag)}"""

        def elem2KeyVal(e):
            key = self.nsstrip(e.tag)
            val = self._type_converter[key](e.text)
            return key, val

        return Epoch(**{key: val
                        for key, val in map(elem2KeyVal, el)})

    @classmethod
    def content(cls, epochs: List[Epoch]) -> dict:  # type: ignore
        return {
            'epoch': [
                epoch.content
                for epoch in epochs
            ]
        }

    def get_content(self):
        """return begin and end time of each epoch as
        well as the number of first and last block"""
        epochs = []
        for epch in self.epochs:
            epochs.append({
                'beginTime': epch.beginTime,
                'endTime': epch.endTime,
                'firstBlock': epch.firstBlock,
                'lastBlock': epch.lastBlock
            })
        return epochs

    def get_serializable_content(self):
        """return a serializable object containing
        begin and end time of each epoch as well
        as the number of first and last block"""
        return copy.deepcopy(self.get_content())

    def associate_categories(self, categories):
        """
        populate epoch.name for each epoch with its corresponding category name

        Retrieve category names from each epoch from a sorted list of
        categories and set epoch.name for each corresponding epoch. If number
        of categories does not match number of epochs, epoch names are
        unchanged.

        **Arguments**

        * **`categories`**: `Categories` from which to extract category names
        """
        # Sort categories
        sorted_categories = categories.sort_categories_by_starttime()
        # Add category names to epochs
        if len(sorted_categories) == len(self):
            for epoch, category in zip(self.epochs, sorted_categories):
                epoch.name = category['category']
        else:
            print(f'Number of categories ({len(sorted_categories)}) does not '
                  f'match number of epochs ({len(self)}). `Epoch.name` will '
                  'default to "epoch" for all epochs.')


class EventTrack(XML):

    _xmlns = r'{http://www.egi.com/event_mff}'
    _xmlroottag = r'eventTrack'
    _default_filename = 'Events.xml'
    _event_type_reverter = {
        'beginTime': XML._dump_datetime,
        'duration': str,
        'relativeBeginTime': str,
        'segmentationEvent': lambda t: ('true' if t else 'false'),
        'code': str,
        'label': str,
        'description': str,
        'sourceDevice': str
    }

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
            'long': np.int64,
            'string': str,
            'TEXT': str,
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
        assert self.nsstrip(events_el.tag) == 'event', f"""
        Unknown event with tag {self.nsstrip(events_el.tag)}"""
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

    @classmethod
    def content(cls, name: str, trackType: str,  # type: ignore
                events: List[dict]) -> dict:
        """return content in xml-convertible json format

        Note
        ----
        `events` is a list dicts with specials keys, none of which are
        required, for example:
        ```
        events = [
            {
                'beginTime': <datetime object>,
                'duration': <int in ms>,
                'relativeBeginTime': <int in ms>,
                'code': <str>,
                'label': <str>
            }
        ]
        ```
        """
        formatted_events = []
        for event in events:
            formatted = {}
            for k, v in event.items():
                assert k in cls._event_type_reverter, f"event property '{k}' "
                "not serializable.  Needs to be on of "
                "{list(cls._event_type_reverter.keys())}"
                formatted[k] = {
                    TEXT: cls._event_type_reverter[k](v)  # type: ignore
                }
            formatted_events.append({TEXT: formatted})
        return {
            'name': {TEXT: name},
            'trackType': {TEXT: trackType},
            'event': formatted_events
        }

    def get_content(self):
        """return the name, type and info on
        the events read from the .xml"""
        return {
            'name': self.name,
            'trackType': self.trackType,
            'event': self.events
        }

    def get_serializable_content(self):
        """return a serializable object containing the name,
        type and info on the events read from the .xml"""
        content = copy.deepcopy(self.get_content())
        for evt in content['event']:
            evt['beginTime'] = XML._dump_datetime(evt['beginTime'])
        return content


class Categories(XML):
    """Parser for 'categories.xml' file

    These files have the following structure:
    ```
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <categories xmlns="http://www.egi.com/categories_mff"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
                        <channels signalBin="1" exclusion="badChannels">
                        1 12 15 50 251 253</channels>
                    </channelStatus>
                    <keys />
                </seg>
                ...
    ```
    """

    _xmlns = r'{http://www.egi.com/categories_mff}'
    _xmlroottag = r'categories'
    _default_filename = 'categories.xml'
    _type_converter = {
        'long': int,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._segment_converter = {
            'beginTime': lambda e: int(e.text),
            'endTime': lambda e: int(e.text),
            'evtBegin': lambda e: int(e.text),
            'evtEnd': lambda e: int(e.text),
            'channelStatus': self._parse_channel_status,
        }
        self._optional_segment_converter = {
            'name': lambda e: str(e.text),
            'keys': self._parse_keys,
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
        """parse and return element <cat>

        Contains <name /> and a <segments />
        """
        assert self.nsstrip(cat_el.tag) == 'cat', f"""
        Unknown cat with tag {self.nsstrip(cat_el.tag)}"""
        name = self.find('name', cat_el).text
        segment_els = self.findall('seg', self.find('segments', cat_el))
        segments = [self._parse_segment(seg_el) for seg_el in segment_els]
        return name, segments

    def _parse_channel_status(self, status_el):
        """parse element <channelStatus>

        Contains <channels />
        """
        def parse_channel_element(element):
            """return parsed channel element"""
            text = element.text or ''
            indices = list(map(int, text.split()))
            channel = {'channels': indices}
            for prop, converter in self._channel_prop_converter.items():
                channel[prop] = converter(element.get(prop))

            return channel

        channels = self.findall('channels', status_el)
        ret = list(map(parse_channel_element, channels))
        return ret or None

    def _parse_faults(self, faults_el):
        """parse element <faults>

        Contains a bunch of <fault />"""
        faults = [el.text for el in self.findall('fault', faults_el)]
        return faults or None

    def _parse_keys(self, keys_el):
        keys = {}
        for key_el in self.findall('key', keys_el):
            keyCode = self.find('keyCode', key_el).text
            data_el = self.find('data', key_el)
            dtype = data_el.get('dataType')
            data = self._type_converter.get(dtype, lambda s: s)(data_el.text)
            keys[keyCode] = {
                'data': data,
                'type': dtype
            }

        return keys or None

    def _parse_segment(self, seg_el):
        """parse element <seg>

        A <seg> element is expected to contain all elements in
        `self._segment_converter.keys()`, and can additionally contain elements
        in `self._optional_segment_converter.keys()`.
        """
        ret = {'status': seg_el.get('status', None)}
        for tag, converter in self._segment_converter.items():
            val = converter(self.find(tag, seg_el))
            ret[tag] = converter(self.find(tag, seg_el))

        for tag, converter in self._optional_segment_converter.items():
            el = self.find(tag, seg_el)
            val = converter(el) if el is not None else None
            if val:
                ret[tag] = val

        return ret

    def get_content(self):
        """return categories related info"""
        return {
            'categories': self.categories
        }

    def get_serializable_content(self):
        """return a serializable object
        containing categories related info"""
        return copy.deepcopy(self.get_content())

    def sort_categories_by_starttime(self) -> List[dict]:
        """return a list of dict `{category: name, t0: starttime}`
        for each data block"""
        sorted_categories = []
        for name, cat in self.categories.items():
            for block in cat:
                sorted_categories.append(
                    {'category': name, 't0': block['beginTime']})
        sorted_categories.sort(key=lambda b: b['t0'])
        return sorted_categories

    @classmethod
    def content(cls, categories):
        """return content of `categories` ready for dict2xml

        **Arguments**

        * **`categories`**: dict containing all infos for "categories.xml"

        **Returns**

        dict that can be passed into `dict2xml.dict2xml` to convert the
        information to an .xml file that follows the specification in
        "schemata/categories.xsd".

        **Example**

        Here's an example dict for `categories`:

        ```python
        expected_categories = {
            'first category': [
                {
                    'status': 'bad',
                    'name': 'Average',
                    'faults': ['eyeb'],
                    'beginTime': 0,
                    'endTime': 1200000,
                    'evtBegin': 205135,
                    'evtEnd': 310153,
                    'channelStatus': [
                        {
                            'signalBin': 1,
                            'exclusion': 'badChannels',
                            'channels': [1, 12, 25, 55]
                        }
                    ],
                    'keys': {
                        '#seg': {
                            'type': 'long',
                            'data': 3
                        },
                        'subj': {
                            'type': 'person',
                            'data': 'RM271_noise_test'
                        }
                    }
                }
            ],
        }
        ```
        """
        return {'cat': [
            cls.serialize_category(name, segments)
            for name, segments in categories.items()
        ]}

    @classmethod
    def serialize_category(cls, name, segments):
        """return serialized category `name` with `segments`"""
        name = {TEXT: str(name)}
        seg = list(map(cls.serialize_segment, segments))
        segments = {TEXT: {'seg': seg}}
        return {
            TEXT: {
                'name': name,
                'segments': segments
            }
        }

    @staticmethod
    def serialize_segment(segment):
        """return serialized segment"""
        text = {}
        output = {TEXT: text}
        # In the following we'll modify `text`

        required_integer_props = [
            'beginTime',
            'endTime',
            'evtBegin',
            'evtEnd'
        ]
        for prop in required_integer_props:
            text[prop] = {TEXT: str(int(segment[prop]))}

        # Add optionals:
        #
        # - status
        # - name
        # - faults
        # - channelStatus
        # - keys
        if 'status' in segment:
            output[ATTR] = {'status': segment['status']}

        if 'name' in segment:
            text['name'] = {TEXT: str(segment['name'])}

        if 'faults' in segment:
            fault_list = [
                {TEXT: fault} for fault in segment['faults']
            ]
            text['faults'] = {
                TEXT: {'fault': fault_list}
            }

        if 'channelStatus' in segment:
            channels_list = []
            for status in segment['channelStatus']:
                attributes = {
                    'signalBin': str(int(status['signalBin'])),
                    'exclusion': status['exclusion']
                }
                channels = ' '.join(map(str, status['channels']))
                channels = {ATTR: attributes, TEXT: channels}
                channels_list.append(channels)
            text['channelStatus'] = {TEXT: {'channels': channels_list}}

        if 'keys' in segment:
            # convert xml element 'data'
            keys_by_code = {
                keyCode: {
                    ATTR: {'dataType': key['type']},
                    TEXT: str(key['data'])
                } for keyCode, key in segment['keys'].items()
            }
            # convert xml element 'keyCode'
            key_list = [{
                'keyCode': {TEXT: keyCode},
                'data': data
            } for keyCode, data in keys_by_code.items()]
            # convert xml element list
            key_list = [{TEXT: item} for item in key_list]
            # add to output
            text['keys'] = {TEXT: {'key': key_list}}

        return output


class DipoleSet(XML):
    """Parser for 'dipoleSet.xml' file

    These files have the following structure:
    ```
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <dipoleSet xmlns="http://www.egi.com/dipoleSet_mff"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <name>SWS_003_IHM</name>
        <type>Dense</type>
        <dipoles>
            <dipole>
                <computationCoordinate>64,1.2e+02,1.5e+02</computationCoordinate>
                <visualizationCoordinate>61,1.4e+02,1.5e+02</visualizationCoordinate>
                <orientationVector>0.25,0.35,0.9</orientationVector>
            </dipole>
            <dipole>
            ...
    ```
    """

    _xmlns = r'{http://www.egi.com/dipoleSet_mff}'
    _xmlroottag = r'dipoleSet'
    _default_filename = 'dipoleSet.xml'

    @property
    def computationCoordinate(self) -> np.ndarray:
        """return computation coordinates"""
        return self.dipoles['computationCoordinate']

    @property
    def visualizationCoordinate(self) -> np.ndarray:
        """return visualization coordinates"""
        return self.dipoles['visualizationCoordinate']

    @property
    def orientationVector(self) -> np.ndarray:
        """return orientation vectors of dipoles"""
        return self.dipoles['orientationVector']

    def __len__(self) -> int:
        """return number of dipoles"""
        return self.dipoles['computationCoordinate'].shape[0]

    @cached_property
    def name(self) -> str:
        """return value of the name tag"""
        return self.find('name').text

    @cached_property
    def type(self) -> str:
        """return value of the type tag"""
        return self.find('type').text

    @cached_property
    def dipoles(self) -> Dict[str, np.ndarray]:
        """return dipoles read from the .xml

        Dipole elements are expected to have a homogenuous number of elements
        such as 'computationCoordinate', 'visualizationCoordinate', and
        'orientationVector'.  The text of each element is expected to be three
        comma-separated floats in scientific notation."""
        dipoles_tag = self.find('dipoles')
        dipole_tags = self.findall('dipole', root=dipoles_tag)
        dipoles: Dict[str, list] = defaultdict(list)
        for tag in dipole_tags:
            for attr in tag.findall('*'):
                tag = self.nsstrip(attr.tag)
                v3 = list(map(float, attr.text.split(',')))
                dipoles[tag].append(v3)
        d_arrays = {
            tag: np.array(lists, dtype=np.float32)
            for tag, lists in dipoles.items()
        }

        # check that all dipole attributes have same lengths and 3 components
        shp = (len(dipole_tags), 3)
        assert all(v.shape == shp for v in d_arrays.values()), f"""
        Parsing dipoles result in broken shape.  Found {[(k, v.shape) for k, v
        in d_arrays.items()]}"""
        return d_arrays

    def get_content(self):
        """return name, type and coordinates
        of the dipole set read from the .xml"""
        return {
            'name': self.name,
            'type': self.type,
            'dipoles': self.dipoles
        }

    def get_serializable_content(self):
        """return a serializable object containing
        the name, type and coordinates of the dipole
        set read from the .xml"""
        content = copy.deepcopy(self.get_content())
        content['dipoles'] = {
            key: value.tolist()
            for key, value in content['dipoles'].items()
        }
        return content


class History(XML):
    """Parser for 'history.xml' files

    These files have the following structure:
    ```
    <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <historyEntries xmlns="http://www.egi.com/history_mff"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <entry>
            <tool>
                <name>example</name>
                <method>Segmentation</method>
                <version>5.4.3-R</version>
                <beginTime>2020-08-27T13:32:26.008693-07:00</beginTime>
                <endTime>2020-08-27T13:32:26.113988-07:00</endTime>
                <sourceFiles>
                    <filePath type="" creator="">/Users/egi/Desktop/
                        RM271_noise_test_20190501_105754.mff</filePath>
                </sourceFiles>
                <settings>
                    <setting>  1: Rules for category
                        &quot;Category A&quot;</setting>
                    ...
    ```
    """

    _xmlns = '{http://www.egi.com/history_mff}'
    _xmlroottag = 'historyEntries'
    _default_filename = 'history.xml'
    _entry_type_reverter = {
        'name': str,
        'kind': str,
        'method': str,
        'version': str,
        'beginTime': XML._dump_datetime,
        'endTime': XML._dump_datetime,
        'sourceFiles': lambda e: {'filePath': [{TEXT: filepath}
                                               for filepath in e]},
        'settings': lambda e: {'setting': [{TEXT: setting} for setting in e]},
        'results': lambda e: {'result': [{TEXT: result} for result in e]}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entry_type_converter = {
            'name': lambda e: str(e.text),
            'kind': lambda e: str(e.text),
            'method': lambda e: str(e.text),
            'version': lambda e: str(e.text),
            'beginTime': lambda e: self._parse_time_str(e.text),
            'endTime': lambda e: self._parse_time_str(e.text),
            'sourceFiles': lambda e: [filepath.text for filepath in
                                      self.findall('filePath', e)],
            'settings': lambda e: [setting.text for setting in
                                   self.findall('setting', e)],
            'results': lambda e: [result.text for result in
                                  self.findall('result', e)]
        }

    def __getitem__(self, idx):
        return self.entries[idx]

    def __len__(self):
        return len(self.entries)

    @cached_property
    def entries(self):
        return [self._parse_entry(entry) for entry in self.findall('entry')]

    def _parse_entry(self, entry_el):
        assert self.nsstrip(entry_el.tag) == 'entry', f"""
        Unknown tool with tag {self.nsstrip(entry_el.tag)}"""
        tool_el = self.find('tool', entry_el)
        return {
            tag: self._entry_type_converter[tag](el)
            for tag, el in map(lambda e: (self.nsstrip(e.tag), e), tool_el)
        }

    @classmethod
    def content(cls, entries: List[dict]) -> dict:  # type: ignore
        """return content in xml-convertible json format

        Note
        ----
        `entries` is a list of dicts with several keys, none of which are
        required. `entries` should have the following structure:
        ```
        entries = [
            {
                'name': <str>,
                'kind': <str>,
                'method': <str>,
                'version': <str>,
                'beginTime': <datetime object>,
                'endTime': <datetime object>,
                'sourceFiles': <List[str]>,
                'settings': <List[str]>,
                'results': <List[str]>
            }
        ]
        ```
        """
        formatted_entries = []
        for entry in entries:
            formatted = {}
            for tag, text in entry.items():
                assert tag in cls._entry_type_reverter, "entry property "
                f"'{text}' not serializable. Needs to be one of "
                f"{list(cls._entry_type_reverter.keys())}."
                formatted[tag] = {
                    TEXT: cls._entry_type_reverter[tag](text)  # type: ignore
                }
            formatted_entries.append({TEXT: formatted})
        return {
            'entry': [
                {
                    TEXT: {
                        'tool': e
                    }
                }
                for e in formatted_entries
            ]
        }

    def get_content(self):
        """return history entries"""
        formatted_entries = []
        for entry in self.entries:
            entry['beginTime'] = self._dump_datetime(entry['beginTime'])
            entry['endTime'] = self._dump_datetime(entry['endTime'])
            formatted_entries.append(entry)
        return formatted_entries

    def get_serializable_content(self):
        """return a serializable object containing history entries"""
        return copy.deepcopy(self.get_content())

    def mff_flavor(self) -> str:
        """return either 'continuous', 'segmented',
        or 'averaged' representing mff flavor"""
        methods = [entry['method'].lower() for entry in self.entries]
        if 'averaging' in methods:
            return 'averaged'
        elif 'segmentation' in methods:
            return 'segmented'
        else:
            return 'continuous'
