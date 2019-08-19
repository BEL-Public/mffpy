#!/usr/bin/env python
"""
`$ zip -Z store -r -j <path>/<name>.mfz <path>/<name>.mff`

Explanation of the zip command:
    -Z store : no compression
    -r : recursive
    -j : remove relative path names
"""
from os.path import splitext, exists, join, basename
from glob import glob
from zipfile import ZipFile, ZIP_STORED
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('filename', type=str, help="Path to .mff directory")
# Check .mff input
input_filename = parser.parse_args().filename
dir_and_base, ext = splitext(input_filename.rstrip('/'))
assert ext.lower() == '.mff', """
'%s' is not a valid .mff directory
""" % input_filename
# Create and check .mfz output filename
output_filename = dir_and_base + '.mfz'
assert not exists(output_filename), """
Output file name '%s' exists already
""" % output_filename

s = "Storing the following files in '%s':" % output_filename
print('\n'.join(['-'*len(s), s, '-'*len(s)]))
with ZipFile(output_filename, mode='w', compression=ZIP_STORED) as zf:
    for content_filename in glob(join(input_filename, '*')):
        print(">", content_filename)
        arc_filename = basename(content_filename)
        zf.write(content_filename, arcname=arc_filename)
print('-'*len(s))
