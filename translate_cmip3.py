# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Translate a stream of filepaths from CMIP3 to CMIP5 syntax
"""


import sys

from isenes.drslib import cmip3, cmip5

translator = cmip3.make_translator('')
cmip5_translator = cmip5.make_translator('')

def main():
    paths = set()
    for line in sys.stdin:
        filename, size = line.strip().split()
        fn = convert(filename)
        
        # Make sure no duplicate paths are created
        assert fn not in paths
        paths.add(fn)
    
def convert(filepath):
    drs = translator.filepath_to_drs(filepath)
    cmip5_filepath = cmip5_translator.drs_to_filepath(drs)

    print '%s --> %s' % (filepath, cmip5_filepath)
    
    return cmip5_filepath

if __name__ == '__main__':
    main()