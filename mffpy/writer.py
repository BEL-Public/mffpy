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
from os import makedirs
from os.path import splitext, exists, join
from subprocess import check_output
import xml.etree.ElementTree as ET

from typing import Dict, Any

from .dict2xml import dict2xml
from .xml_files import XML
from .bin_writer import BinWriter, StreamingBinWriter
from .devices import coordinates_and_sensor_layout
import json

__all__ = ['Writer', 'BinWriter', 'StreamingBinWriter']


class Writer:

    def __init__(self, filename: str):
        self.filename = filename
        self.files: Dict[str, Any] = {}
        self._bin_file_added = False
        self.mffdir, self.ext = splitext(self.filename)
        self.mffdir += '.mff'
        self.file_created = False

    def create_directory(self):
        """Creates the directory for the recording."""
        if not self.file_created:
            makedirs(self.mffdir, exist_ok=False)
            self.file_created = True

    def write(self):
        """write contents to .mff/.mfz file"""

        self.create_directory()

        # write .xml/.bin files.  For .xml files we need to set the default
        # namespace to avoid `ns0:` being prepended to each tag.
        for filename, (content, typ) in self.files.items():
            if '.xml' == splitext(filename)[1]:
                ET.register_namespace('', typ._xmlns[1:-1])
            content.write(join(self.mffdir, filename), encoding='UTF-8',
                          xml_declaration=True, method='xml')

        # convert from .mff to .mfz
        if self.ext == '.mfz':
            check_output(['mff2mfz.py', self.mffdir])
        
    def export_to_json(self, data):
        """export data to .json file"""
        # create .json file
        with open(self.filename, 'w') as file:
            json.dump(data, file, indent=4)

    def addxml(self, xmltype, filename=None, **kwargs):
        """Add an .xml file to the collection

        **Parameters**

        *xmltype*: determines to which `XML.todict` the kwargs are passed
        *filename*: (defaults `content['filename']`) filename of the xml file
        """
        content = XML.todict(xmltype, **kwargs)
        content_filename = content.pop('filename')
        filename = filename or content_filename
        self.files[filename] = (
            dict2xml(**content), type(XML)._tag_registry[xmltype])

    def addbin(self, binfile: BinWriter, filename=None):
        """Add the .bin file to the collection

        Currently we only allow to add one such files, b/c .mff can only have
        one `epochs` file.  For this we added the flag `self._bin_file_added`.

        **Parameters**

        *binfile*: `class BinWriter` to be added to the collection
        *filename*: (defaults to `binfile.default_filename`) filename of the
            bin file.  It's not recommended to change this default value.
        """
        assert not self._bin_file_added
        self.files[filename or binfile.default_filename] = (
            binfile, type(binfile))
        self.addxml('dataInfo', **binfile.get_info_kwargs())
        self.addxml('epochs', epochs=binfile.epochs)
        self._bin_file_added = True

    def add_coordinates_and_sensor_layout(self, device: str) -> None:
        """Add coordinates.xml and sensorLayout.xml to the writer

        **Parameters**

        *device*: name string of a device.  Valid choices are in
        "mffpy/resources/coordinates".
        """
        xmls = coordinates_and_sensor_layout(device)
        for name, xml in xmls.items():
            self.files[name + '.xml'] = (ET.ElementTree(xml.root), type(xml))

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter  # type: ignore
    def filename(self, fn: str):
        """check filename with .mff/.mfz extension does not exist"""
        base, ext = splitext(fn)
        assert ext in ('.mff', '.mfz', '.json')
        assert not exists(fn), f"File '{fn}' exists already"
        if ext == '.mfz':
            assert not exists(base + '.mff')
        self._filename = fn
