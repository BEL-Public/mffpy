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
from os.path import basename, splitext, exists, join

import numpy as np
import pytest

from ..devices import coordinates_and_sensor_layout, resources_dir


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
])
def test_devices(device):
    """test integrity of coordinates.xml locations for each supported device

    For each device, all electrode locations are compared against
    the hashed values in 'mffpy/resources/testing'"""
    xmls = coordinates_and_sensor_layout(device)
    coords = xmls['coordinates']
    locs = np.array([
        np.array([props['x'], props['y'], props['z']])
        for i, (_, props) in enumerate(coords.sensors.items())
    ], dtype=np.float)
    device = basename(splitext(device)[0]) if exists(device) else device
    expected = np.load(join(resources_dir, 'testing', device+'.npy'),
                       allow_pickle=True)
    assert locs.shape == expected.shape
    assert locs == pytest.approx(expected)
