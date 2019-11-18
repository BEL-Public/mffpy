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

"""
This script is used to export the contents of an MFF file into a JSON format.

@author: Damian Persico - persicodamian@gmail.com
"""

from os.path import splitext, sep
from mffpy import Reader, Writer
from argparse import ArgumentParser


def mff2json(input_filename):
    if input_filename:
        # Check .mff input
        dir_and_base, ext = splitext(input_filename.rstrip(sep))
        assert ext.lower() == '.mff', f"{input_filename} is not a valid .mff directory"
        output_filename = dir_and_base + '.json'

        # Read data from an MFF file
        reader = Reader(input_filename)
        print("Reading data from " + str(input_filename))
        data = reader.get_mff_content()

        # Write data into a JSON file
        writer = Writer(output_filename)
        print("Writing data out to " + str(output_filename))
        writer.export_to_json(data)
    else:
        print("No .mff file provided.\nPlease, provide a path to a valid .mff directory")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--mff_file", type=str, help="Path to an MFF directory")
    mff2json(parser.parse_args().mff_file)
