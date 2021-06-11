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

from glob import glob
import os.path as op
from zipfile import ZipFile, ZIP_STORED

import pytest


@pytest.fixture(scope='session', autouse=True)
def ensure_mfz():
    """Ensure that the mfz file exists."""
    fname = op.join(
        op.dirname(__file__), '..', '..', 'examples', 'example_1.mfz')
    if not op.isfile(fname):
        with ZipFile(fname, mode='w', compression=ZIP_STORED) as zf:
            for content_filename in glob(op.join(fname[:-3] + 'mff', '*')):
                arc_filename = op.basename(content_filename)
                zf.write(content_filename, arcname=arc_filename)
