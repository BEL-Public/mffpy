
from os import makedirs
from os.path import splitext, exists, join
from subprocess import check_output
import xml.etree.ElementTree as ET

from typing import Dict, Any

from .dict2xml import dict2xml
from .xml_files import XML
from .bin_writer import BinWriter
from .devices import coordinates_and_sensor_layout

__all__ = ['Writer', 'BinWriter']


class Writer:

    def __init__(self, filename: str):
        self.filename = filename
        self.files: Dict[str, Any] = {}
        self._bin_file_added = False

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter  # type: ignore
    def filename(self, fn: str):
        """check filename with .mff/.mfz extension does not exists"""
        base, ext = splitext(fn)
        assert ext in ('.mff', '.mfz')
        assert not exists(fn), f"File '{fn}' exists already"
        if ext == '.mfz':
            assert not exists(base + '.mff')
        self._filename = fn

    def addxml(self, xmltype, filename=None, **kwargs):
        """Add an .xml file to the collection

        **Parameters**

        *xmltype*: determines to which `XML.todict` the kwargs are passed
        *filename*: (defaults `content['filename']`) filename of the xml file
        """
        content = XML.todict(xmltype, **kwargs)
        content_filename = content.pop('filename')
        filename = filename or content_filename
        self.files[filename] = dict2xml(**content)

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
        self.files[filename or binfile.default_filename] = binfile
        self.addxml('dataInfo', **binfile.get_info_kwargs())
        self.addxml('epochs', epochs=binfile.epochs)
        self._bin_file_added = True

    def add_coordinates_and_sensor_layout(self, device: str,
                                          filename: str = None):
        """Add coordinates.xml and sensorLayout.xml to the writer

        **Parameters**

        *device*: either the valid name of a device, or a file path
        *filename* (optional): the name under which the layout should
            be stored inside the .mff file.
        """
        xmls = coordinates_and_sensor_layout(device)
        for name, xml in xmls.items():
            self.files[name + '.xml'] = ET.ElementTree(xml.root)

    def write(self):
        """write contents to .mff/.mfz file"""
        # create .mff directory
        mffdir, ext = splitext(self.filename)
        mffdir += '.mff'
        makedirs(mffdir, exist_ok=False)

        # write .xml/.bin files
        for filename, content in self.files.items():
            content.write(join(mffdir, filename), encoding='UTF-8',
                          xml_declaration=True, method='xml')

        # convert from .mff to .mfz
        if ext == '.mfz':
            check_output(['mff2mfz.py', mffdir])
