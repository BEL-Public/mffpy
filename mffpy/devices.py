
from os.path import dirname, exists, join

from .xml_files import XML, Coordinates

resources_dir = join(dirname(__file__), 'resources')


def sensor_layout(device: str):
    if not exists(device):
        filename = join(resources_dir, device + '.xml')
        assert exists(filename), f"Sensor layout of {device} not available"
    else:
        filename = device
    xml = XML.from_file(filename)
    assert isinstance(xml, Coordinates), f"""
    file {device} not of type Coordinates [{type(xml)}]"""
    return xml
