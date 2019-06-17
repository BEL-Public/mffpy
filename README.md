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
Name                          Stmts   Miss  Cover
-------------------------------------------------
mffpy/__init__.py                 2      0   100%
mffpy/bin_files.py               41      8    80%
mffpy/mffdir.py                  96     18    81%
mffpy/raw_bin_files.py          131      2    98%
mffpy/reader.py                  57      2    96%
mffpy/test_mffdir.py             30      0   100%
mffpy/test_raw_bin_files.py      36      0   100%
mffpy/test_reader.py             20      0   100%
mffpy/test_xml_files.py          97      1    99%
mffpy/test_zipfile.py            34      0   100%
mffpy/xml_files.py              257     16    94%
mffpy/zipfile.py                 45      0   100%
-------------------------------------------------
TOTAL                           846     47    94%
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

# write 10 channels of 512 data points at a sampling rate of 128 Hz
B = BinWriter(sampling_rate=128)
B.add_block(np.random.randn(10, 512).astype(np.float32))
W = Writer(join('examples', 'copy.mff'))
startdatetime = datetime.strptime('1984-02-18T14:00:10.000000+0100',
        "%Y-%m-%dT%H:%M:%S.%f%z")
W.addxml('fileInfo', recordTime=startdatetime)
W.addbin(B)
W.write()
```
