
from os.path import basename, splitext, exists, join

import numpy as np
import pytest

from ..devices import sensor_layout, resources_dir


@pytest.mark.parametrize("device", [
    'Geodesic Sensor Net 64 2.0',
    'Geodesic Sensor Net 128 2.1',
    'Geodesic Sensor Net 256 2.1',
    'HydroCel GSN 32 1.0',
    'HydroCel GSN 64 1.0',
    'HydroCel GSN 128 1.0',
    'HydroCel GSN 256 1.0',
    'MicroCel GSN 100 32 1.0',
    'MicroCel GSN 100 64 1.0',
    'MicroCel GSN 100 128 1.0',
    'MicroCel GSN 100 256 1.0',
    # test also that `sensor_layout` accepts full paths
    join(resources_dir, 'MicroCel GSN 100 256 1.0.xml'),
])
def test_devices(device):
    """test integrity of locations for each supported device

    For each device, all electrode locations are compared against
    the hashed values in 'mffpy/resources/testing'"""
    layout = sensor_layout(device)
    locs = np.array([
        np.array([props['x'], props['y'], props['z']])
        for i, (_, props) in enumerate(layout.sensors.items())
    ], dtype=np.float)
    device = basename(splitext(device)[0]) if exists(device) else device
    expected = np.load(join(resources_dir, 'testing', device+'.npy'))
    assert locs.shape == expected.shape
    assert locs == pytest.approx(expected)
