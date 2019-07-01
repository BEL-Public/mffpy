
from os.path import dirname, exists, join

from .xml_files import XML

resources_dir = join(dirname(__file__), 'resources')


def coordinates_and_sensor_layout(device: str):
    xml = {}
    for name in ('coordinates', 'sensorLayout'):
        filename = join(resources_dir, name, device + '.xml')
        assert exists(filename), f"{name} of {device} not available"
        xml[name] = XML.from_file(filename)
    return xml
