#!/usr/bin/env python
"""
Quick command-line script for creating datasets from listings files.
This uses the gen_drs module in tests.

Usage: make_listing.py dest-dir listing_file

"""

import sys

from test.gen_drs import write_listing

def main(argv=sys.argv):
    dest_dir, listing = argv[1:]

    write_listing(dest_dir, listing)

if __name__ == '__main__':
    main()


