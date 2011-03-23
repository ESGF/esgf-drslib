#!/usr/bin/env python
# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

Randomly sample a CMIP listing file

Usage: sample_listing.py n <listing.txt

"""

import sys, random

def main():
    n = int(sys.argv[1])

    fns = []
    for line in sys.stdin:
        fn, size = line.strip().split()
        fns.append(fn)

    s = random.sample(fns, n)
    for fn in s:
        print fn

if __name__ == '__main__':
    main()