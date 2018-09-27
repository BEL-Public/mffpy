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
    _time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
    
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
        # convert
        # <   2003-04-17T13:35:22.000000-08:00
        # >   2003-04-17T13:35:22.000000-0800
        txt = txt[::-1].replace(':', '', 1)[::-1] 
        return datetime.strptime(txt, self._time_format)



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
