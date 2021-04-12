#!/usr/bin/env python
"""
mffdiff.py

Compare the content of two mff files
"""
from os.path import join
from subprocess import check_output
from mffpy import Reader
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('leftpath', type=str, help="MFF file to compare")
parser.add_argument('rightpath', type=str, help="second MFF file to compare")
args = parser.parse_args()

left_mff = Reader(args.leftpath)
right_mff = Reader(args.rightpath)


def getnested(cls, props, callback=None):
    if props:
        val = getattr(cls, props[0])
        return getnested(val, props[1:], callback)

    return callback(cls) if callback else cls


def compare_raw(filename):
    leftfile = join(args.leftpath, filename)
    rightfile = join(args.rightpath, filename)
    try:
        check_output(['diff', leftfile, rightfile])
        status = 'match'
    except BaseException:
        status = 'diff'

    print(f">>> {status} @ file '{filename}'")


def compare(prop, callback=None, info=''):
    props = prop.split('.')
    try:
        left_value = getnested(left_mff, props, callback)
        right_value = getnested(right_mff, props, callback)
        left_msg = str(left_value)[:50]
        right_msg = str(right_value)[:50]
        if left_value != right_value:
            msg = f'\t{left_msg} != {right_msg}'
            status = 'diff'
        else:
            msg = ''
            status = 'match'

    except BaseException as err:
        status = 'error'
        msg = str(err)[:50] + '\n'
        left_value = None

    print(f">>> {status} @ reader_instance.{prop} "
          f"{': ' + info if info else ''}")
    if msg:
        print(msg)

    return left_value if status == 'match' else None


print(f"Comparing {args.leftpath} with {args.rightpath}")
compare('flavor')
compare('sampling_rates')
compare('durations')
compare('startdatetime')
compare('units')
compare('num_channels')
compare('categories.categories')
epoch_count = compare('epochs.epochs', lambda e: len(e), 'len(..)')
if epoch_count is not None:
    for i in range(epoch_count):
        compare('epochs.epochs', lambda e: e[i].content, f"[{i}].content")

out = compare_raw('signal1.bin')
