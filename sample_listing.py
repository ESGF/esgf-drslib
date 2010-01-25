#!/usr/bin/env python
"""
Randomly sample a CMIP listing file

Usage: sample_listing.py n <listing.txt

"""

import sys, random

n = int(sys.argv[1])

fns = []
for line in sys.stdin:
    fn, size = line.strip().split()
    fns.append(fn)

s = random.sample(fns, n)
for fn in s:
    print fn
