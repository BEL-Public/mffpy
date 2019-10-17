"""
This script is used to export the contents of an MFF file into a JSON format.

@author: Damian Persico - persicodamian@gmail.com

Copyright © 2019 The Brain Electrophysiology Laboratory Company. All rights reserved.
"""

from os.path import splitext
from mffpy import Reader, Writer
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--mff_file", type=str, help="Path to an MFF directory")
    return parser.parse_args()


if __name__ == "__main__":
    input_filename = parse_args().mff_file

    if input_filename:
        # Check .mff input
        dir_and_base, ext = splitext(input_filename.rstrip('/'))
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
