#!/usr/bin/env python
"""
mffdiff.py

Compare the content of two mff files
"""
from mffpy import Reader

leftpath = "examples/example_1.mff"
rightpath = "examples/example_3.mff"

left_mff = Reader(leftpath)
right_mff = Reader(rightpath)


def getnested(cls, props):
    if props:
        val = getattr(cls, props[0])
        return getnested(val, props[1:])

    return cls


def compare(prop):
    props = prop.split('.')
    status = 'match'
    msg = ''
    try:
        left_value = getnested(left_mff, props)
        right_value = getnested(right_mff, props)
        left_msg = str(left_value)[:50]
        right_msg = str(right_value)[:50]
        if left_value != right_value:
            msg = f'\t{left_msg} != {right_msg}'
            status = 'diff'

    except BaseException:
        status = 'error'

    print(f'>>> {status} @ reader_instance.{prop}')
    if msg:
        print(msg)


compare('flavor')
compare('categories.categories')
compare('epochs')
compare('sampling_rates')
compare('durations')
compare('startdatetime')
compare('units')
compare('num_channels')
