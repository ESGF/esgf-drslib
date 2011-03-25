# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Strip subset syntax out of CMIP3 runs


Filename types

<var>_<table>_<dddd>
<var>_<table>.<dddddddddd>-<dddddddddd>
<var>_<table>.<model?>.<exp>.<dddd>
<var>_<table>_<d>
<var>_<table>.<dddd>

"""

import sys, os, re

rexp = re.compile(r'(\w+)_(\w+)(?:[._-](.*))?.nc$')

def main():
    for line in sys.stdin:
        filename, size = line.strip().split()
    
        dirname, basename = os.path.split(filename)
    
        mo = rexp.match(basename)
        if not mo:
            print '** %s' % basename
        else:
            print basename, mo.groups()

if __name__ == '__main__':
    main()