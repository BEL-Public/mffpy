
from os import makedirs
from os.path import splitext, exists, join
from subprocess import check_output
import xml.etree.ElementTree as ET

from typing import Dict, Any

from .json2xml import *
from .xml_files import XML


class Writer:

    def __init__(self, filename: str):
        self.filename = filename
        self.xmlfiles: Dict[str, Dict[str, Any]] = {}

    @property
    def filename(self) -> str:
        return self._filename

    def add(self, xmltype, filename=None, **kwargs):
        d = XML.todict(xmltype, **kwargs)
        filename = filename or d.pop('filename')
        self.xmlfiles[filename] = d
    
    @filename.setter # type: ignore
    def filename(self, fn: str):
        """check filename with .mff/.mfz extension does not exists"""
        base, ext = splitext(fn)
        assert ext in ('.mff', '.mfz')
        assert not exists(fn)
        if ext == '.mfz':
            assert not exists(base + '.mff')
        self._filename = fn

    def write(self):
        """write contents to .mff/.mfz file"""
        # create .mff directory
        mffdir, ext = splitext(self.filename)
        mffdir += '.mff'
        makedirs(mffdir)

        # add .xml files from json
        for filename, content in self.xmlfiles.items():
            xml = dict2xml(**content)
            xml.write(join(mffdir, filename), encoding='UTF-8',
                    xml_declaration=True, method='xml')

        # convert from .mff to .mfz
        if ext is '.mfz':
            check_output(['mff2mfz.py', mffdir])
