"""Parsing for all xml files"""

import xml.etree.ElementTree as ET
import base64
import numpy as np
from os.path import splitext
from datetime import datetime

class XMLBase:

    _extensions = ('.xml', '.XML')
    _ext_err = "Unknown file type [extension has to be one of %s]"
    _xmlns = None
    _xmlroottag = None
    _supported_versions = (None,)
    _time_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    @classmethod
    def _parse_time_str(cls, txt):
        # convert time string "2003-04-17T13:35:22.000000-08:00"
        # to "2003-04-17T13:35:22.000000-0800" ..
        txt = txt[::-1].replace(':', '', 1)[::-1] 
        return datetime.strptime(txt, cls._time_format)


    def __init__(self, filename):
        self.filename = filename
        self._check_ext()

    def _check_ext(self):
        assert splitext(self.filename)[1] in self._extensions, self._ext_err%self._extensions

    @property
    def _xml_root(self):
        try:
            return self.__xml_root
        except AttributeError: # no __xml_root
            self.__xml_root = ET.parse(self.filename).getroot()
            assert self.__xml_root.tag == self._xmlns+self._xmlroottag, "XML format in file '%s': root tag '%s' ['%s']."%(self.filename, self.__xml_root.tag, self._xmlns+self._xmlroottag)
            self.query_version()
            return self._xml_root

    def query_version(self):
        raise NotImplementedError

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
    
    def query_version(self):
        el = self.find('mffVersion')
        self._version = None if el is None else el.text

    @property
    def version(self):
        try:
            return self._version
        except AttributeError:
            self.query_version()
            return self.version

    @property
    def recordTime(self):
        try:
            return self._recordTime
        except AttributeError:
            self._recordTime = self._parse_recordTime()
            return self.recordTime

    def _parse_recordTime(self):
        txt = self.find('recordTime').text
        return self._parse_time_str(txt)


class DataInfo(XMLBase):

    _xmlns = r'{http://www.egi.com/info_n_mff}'
    _xmlroottag = r'dataInfo'

    def query_version(self):
        return None

    @property
    def generalInformation(self):
        try:
            return self._generalInformation
        except AttributeError:
            self._generalInformation = self._parse_generalInformation()
            return self.generalInformation

    def _parse_generalInformation(self):
        el = self.find('fileDataType', self.find('generalInformation'))
        el = el[0]
        info = {}
        info['channel_type'] = self.nsstrip(el.tag)
        for el_i in el:
            print(el_i.tag, self.nsstrip(el_i.tag))
            info[self.nsstrip(el_i.tag)] = el_i.text
        return info

    @property
    def filters(self):
        try:
            return self._filters
        except AttributeError:
            self._filters = self._parse_filters()
            return self.filters

    def _parse_filters(self):
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

    @property
    def calibrations(self):
        try:
            return self._calibrations
        except AttributeError:
            self._calibrations = self._parse_calibrations()
            return self.calibrations

    def _parse_calibrations(self):
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

    def query_version(self):
        return None

    @property
    def fields(self):
        try:
            return self._fields
        except AttributeError:
            self._fields = self._parse_fields()
            return self.fields

    def _parse_fields(self):
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

    def query_version(self):
        return None

    @property
    def name(self):
        try:
            return self._name
        except AttributeError:
            self._name = self.get('name').text
            return self.name

    @property
    def sensors(self):
        try:
            return self._sensors
        except AttributeError:
            self._sensors = self._parse_sensors()
            return self.sensors

    def _parse_sensors(self):
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

    @property
    def threads(self):
        try:
            return self._threads
        except AttributeError:
            self._threads = self._parse_threads()
            return self.threads

    def _parse_threads(self):
        ans = []
        for thread in self.find('threads'):
            assert self.nsstrip(thread.tag) == 'thread', "Unknown thread with tag '%s'"%self.nsstrip(thread.tag)
            ans.append(tuple(map(int, thread.text.split(','))))
        return ans

    @property
    def tilingSets(self):
        try:
            return self._tilingSets
        except AttributeError:
            self._tilingSets = self._parse_tilingSets()
            return self.tilingSets

    def _parse_tilingSets(self):
        ans = []
        for tilingSet in self.find('tilingSets'):
            assert self.nsstrip(tilingSet.tag) == 'tilingSet', "Unknown tilingSet with tag '%s'"%self.nsstrip(tilingSet.tag)
            ans.append(list(map(int, tilingSet.text.split())))
        return ans

    @property
    def neighbors(self):
        try:
            return self._neighbors
        except AttributeError:
            self._neighbors = self._parse_neighbors()
            return self.neighbors

    def _parse_neighbors(self):
        ans = {}
        for ch in self.find('neighbors'):
            assert self.nsstrip(ch.tag) == 'ch', "Unknown ch with tag '%s'"%self.nsstrip(ch.tag)
            key = int(ch.get('n'))
            ans[key] = list(map(int, ch.text.split()))
        return ans

    @property
    def mappings(self):
        try:
            return self._mappings
        except AttributeError:
            self._mappings = self._parse_mappings()
            return self.mappings

    def _parse_mappings(self):
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

    def query_version(self):
        return None

    @property
    def acqTime(self):
        try:
            return self._acqTime
        except AttributeError:
            self._acqTime = self._parse_acqTime()
            return self.acqTime

    def _parse_acqTime(self):
        txt = self.find("acqTime").text
        return self._parse_time_str(txt)

    @property
    def acqMethod(self):
        try:
            return self._acqMethod
        except AttributeError:
            self._acqMethod = self._parse_acqMethod()
            return self.acqMethod

    def _parse_acqMethod(self):
        el = self.find("acqMethod")
        return el.text

    @property
    def name(self):
        try:
            return self._name
        except AttributeError:
            self._name = self.get('name').text
            return self.name

    @property
    def defaultSubject(self):
        try:
            return self._defaultSubject
        except AttributeError:
            self._defaultSubject = bool(self.find('defaultSubject').text)
            return self.defaultSubject

    @property
    def sensors(self):
        try:
            return self._sensors
        except AttributeError:
            self._sensors = self._parse_sensors()
            return self.sensors

    def _parse_sensors(self):
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
