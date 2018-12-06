# Introduction

`mffpy` is a lean reader for EGI's MFF file format.  These files are
directories containing several files of mostly xml files, but also binary
files.

The main entry point into the library is class `Reader` that accesses a
selection of functions in the .mff directory to return signal data and its meta
information.

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
f = mffpy.Reader("./examples/example_1.mff")
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
import mffpy
fo = mffpy.Reader("./examples/example_1.mff")
fo.set_unit('EEG', 'uV')
eeg_in_mV, t0_EEG = fo.get_physical_samples_from_epoch(fo.epochs[0], dt=0.1)['EEG']
fo.set_unit('EEG', 'V')
eeg_in_V, t0_EEG = fo.get_physical_samples_from_epoch(fo.epochs[0], dt=0.1)['EEG']
print('data in mV:', eeg_in_mV[0])
print('data in V :', eeg_in_V[0])
```
