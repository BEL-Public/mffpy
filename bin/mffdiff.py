#!/usr/bin/env python
"""
mffdiff.py

Compare the content of two MFF files
"""
from os.path import join
from subprocess import check_output
from mffpy import Reader
from argparse import ArgumentParser

char_limit = 50

parser = ArgumentParser(description="""
compare the contents of two MFF files
""")
parser.add_argument('leftpath', type=str, help="MFF file to compare")
parser.add_argument('rightpath', type=str, help="second MFF file to compare")
args = parser.parse_args()

left_mff = Reader(args.leftpath)
right_mff = Reader(args.rightpath)


def getnested(instance, props, callback=None):
    """get nested property of instance

    This is a recursive function to access a nested property, e.g. for
    `instance.a.b.c`, props is `['a', 'b', 'c']`.  `callback` is optionally
    applied to the final value.

    Parameters
    ----------
        instance:
            instance that has a property `props[0]`
        props:
            nested property split into a list
        callback:
            is optionally applied to the output value
    """
    if props:
        val = getattr(instance, props[0])
        return getnested(val, props[1:], callback)

    return callback(instance) if callback else instance


def compare_raw(filename):
    """compare file in MFF using `$ diff`"""
    leftfile = join(args.leftpath, filename)
    rightfile = join(args.rightpath, filename)
    try:
        check_output(['diff', leftfile, rightfile])
        status = 'match'
    except BaseException:
        status = 'diff'

    print(f">>> {status} @ file '{filename}'")


def compare(prop: str, callback=None, info: str = ''):
    """compare property between left_mff and right_mff

    Parameters
    ----------
        prop:
            string specifying a nested property of `mffpy.Reader` instance
        callback:
            post processing of the value of `prop`
        info:
            additional note of the nested property
    """
    props = prop.split('.')
    try:
        left_value = getnested(left_mff, props, callback)
        right_value = getnested(right_mff, props, callback)
        left_msg = str(left_value)[:char_limit]
        right_msg = str(right_value)[:char_limit]
        if left_value != right_value:
            msg = f'\t{left_msg} != {right_msg}'
            status = 'diff'
        else:
            msg = ''
            status = 'match'

    except BaseException as err:
        status = 'error'
        msg = str(err)[:char_limit] + '\n'
        left_value = None

    print(f">>> {status} @ reader_instance.{prop} "
          f"{': ' + info if info else ''}")
    if msg:
        print(msg)

    return left_value if status == 'match' else None


simple_props = ['mff_flavor', 'sampling_rates', 'durations', 'startdatetime',
                'units', 'num_channels', 'categories.categories']

print(f"Comparing {args.leftpath} with {args.rightpath}")
for prop in simple_props:
    compare(prop)

epoch_count = compare('epochs.epochs', lambda e: len(e), 'len(..)')
if epoch_count is not None:
    for i in range(epoch_count):
        compare('epochs.epochs', lambda e: e[i].content, f"[{i}].content")

out = compare_raw('signal1.bin')
