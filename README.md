# Introduction

[![Build Status](https://semaphoreci.com/api/v1/projects/be4f860e-7b26-45b2-9513-91f75c8081b5/2475430/badge.svg)](https://semaphoreci.com/bel-co/mffpy)

`mffpy` is a lean reader for EGI's MFF file format.  These files are
directories containing several files of mostly xml files, but also binary
files.

The main entry point into the library is class `Reader` that accesses a
selection of functions in the .mff directory to return signal data and its meta
information.

## Installation

```bash
$ conda create -n mffpy python=3.6 pip
$ conda activate mffpy
$ pip install -r requirements.txt
$ python setup.py install
$ # and to run the test
$ make test
```

## Contribute

Definitely run:
```bash
$ pip install pre-commit
$ pre-commit install
```

### Test Coverage

```
Name                                Stmts   Miss  Cover
-------------------------------------------------------
mffpy/__init__.py                       2      0   100%
mffpy/bin_files.py                     40      8    80%
mffpy/bin_writer.py                    47      7    85%
mffpy/devices.py                       10      0   100%
mffpy/dict2xml.py                      31      3    90%
mffpy/epoch.py                         23      5    78%
mffpy/header_block.py                  49      1    98%
mffpy/mffdir.py                        92     18    80%
mffpy/raw_bin_files.py                 95      0   100%
mffpy/reader.py                        57      2    96%
mffpy/tests/__init__.py                 0      0   100%
mffpy/tests/test_devices.py            12      0   100%
mffpy/tests/test_dict2xml.py           15      0   100%
mffpy/tests/test_header_block.py       37      0   100%
mffpy/tests/test_mffdir.py             30      0   100%
mffpy/tests/test_raw_bin_files.py      33      0   100%
mffpy/tests/test_reader.py             26      0   100%
mffpy/tests/test_writer.py             50      2    96%
mffpy/tests/test_xml_files.py         130      1    99%
mffpy/tests/test_zipfile.py            34      0   100%
mffpy/writer.py                        51      2    96%
mffpy/xml_files.py                    325      8    98%
mffpy/zipfile.py                       45      0   100%
-------------------------------------------------------
TOTAL                                1234     57    95%
```

## View the Docs

All documentation and API guidance are generated from the python doc-strings
and this README file using pydoc-markdown.  To view the docs:

* install pydoc-markdown: `pip install pydoc-markdown`
* build and run:  `pydocmd build; pydocmd serve`
* Navigate to the [docs](http://localhost:8000)

## Example Code

### Example 1:  Basic Information

```python
import mffpy
fo = mffpy.Reader("./examples/example_1.mff")
print("time and date of the start of recording:", fo.startdatetime)
print("number of channels:", fo.num_channels)
print("sampling rates:", fo.sampling_rates, "(in Hz)")
print("durations:", fo.durations, "(in sec.)")
print("Here's the epoch information")
for i, e in enumerate(fo.epochs):
    print("Epoch number", i)
    print(e)
```

### Example 2: Reading Samples

```python
from mffpy import Reader
fo = Reader("./examples/example_1.mff")
fo.set_unit('EEG', 'uV')
eeg_in_mV, t0_EEG = fo.get_physical_samples_from_epoch(fo.epochs[0], dt=0.1)['EEG']
fo.set_unit('EEG', 'V')
eeg_in_V, t0_EEG = fo.get_physical_samples_from_epoch(fo.epochs[0], dt=0.1)['EEG']
print('data in mV:', eeg_in_mV[0])
print('data in V :', eeg_in_V[0])
```

### Example 3: Reading .mff xml files

```python
from mffpy import XML
categories = XML.from_file("./examples/example_1.mff/categories.xml")
print(categories['ULRN'])
```

### Example 4: Writing random numbers into an .mff file

```python
from os.path import join
from datetime import datetime
import numpy as np
from mffpy import Reader
from mffpy.writer import *

# write 256 channels of 10 data points at a sampling rate of 128 Hz
B = BinWriter(sampling_rate=128)
B.add_block(np.random.randn(256, 10).astype(np.float32))
W = Writer(join('examples', 'my_new_file.mff'))
startdatetime = datetime.strptime('1984-02-18T14:00:10.000000+0100',
        "%Y-%m-%dT%H:%M:%S.%f%z")
W.addxml('fileInfo', recordTime=startdatetime)
W.add_coordinates_and_sensor_layout(device='HydroCel GSN 256 1.0')
W.addbin(B)
W.write()
```

## License and Copyright

Copyright 2019 Brain Electrophysiology Laboratory Company LLC

Licensed under the ApacheLicense, Version 2.0(the "License");
you may not use this module except in compliance with the License.
You may obtain a copy of the License at:

http: // www.apache.org / licenses / LICENSE - 2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
ANY KIND, either express or implied.