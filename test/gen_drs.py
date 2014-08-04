# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Bulk Generate DRS objects for testing.

"""

import random
from copy import copy
from datetime import datetime
import os, sys

import os.path as op

from drslib.drs import CmipDRS
from drslib import cmip5, config

from itertools import izip

# Python 2.5 compatibility
try:
    from itertools import product
except ImportError:
    def product(*args, **kwds):
        # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
        # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
        pools = map(tuple, args) * kwds.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x+[y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)


def random_drs(drs_template, drs_attr_values):
    """
    Create a random DRS object from a template and a dictionary
    of possible extra attribute values.

    drs_attr_values is a mapping of attribute names to either:
      1. A sequence of possible values
      2. A callable that will return a value

    """
    d = copy(drs_template)

    for attr, values in drs_attr_values:
        if hasattr(values, '__call__'):
            v = values()
        else:
            v = random.choice(values)
        setattr(d, attr, v)

    return v

def iter_random_drs(drs_template, drs_attr_values, limit=None):
    """
    Iterator that generates random DRS objects up to limit or forever.

    """
    i = 0
    while limit is None or i>=limit:
        yield random_drs(drs_template, drs_attr_values)
        i += 1

def iter_drs_template(drs_template, drs_attr_values):
    """
    Iterate over all variations of drs_template with the possible values
    from drs_attr_values.

    """
    #!NOTE: Assuming the ordering is the same
    attrs = drs_attr_values.keys()
    pos_values = drs_attr_values.values()

    for values in product(*pos_values):
        drs = copy(drs_template)
        for attr, value in izip(attrs, values):
            setattr(drs, attr, value)
        yield drs
            
def emember_range(imax, rmax=1, pmax=1):
    for i in xrange(imax):
        for r in xrange(rmax):
            for p in xrange(pmax):
                yield (i+1, r+1, p+1)

def subset_range(date1, date2, clim, n):
    #!NOTE: This uses datetime objects that won't use 360-day calendars.
    #       It therefore isn't suitable for making CMOR-correct filenames
    t_delta = (date2 - date1) / n

    for i in xrange(n):
        dt1 = date1 + t_delta*i
        dt2 = date1 + t_delta*(i+1)
        N1 = (dt1.year, dt1.month, dt1.day, dt1.hour, None, None)
        N2 = (dt2.year, dt2.month, dt2.day, dt2.hour, None, None)
        yield (N1, N2, clim)


def make_eg(**iter_template):
    template = CmipDRS(activity='cmip5', product='output', institute='MOHC',
                       model='HadCM3', experiment='1pctto4x', 
                       frequency='day', realm='atmos', table='day',
                       )
    d = dict(ensemble=emember_range(1), subset=make_subset())
    d.update(iter_template)

    return iter_drs_template(template, d)

def make_subset(y1=2000, y2=2010, n=5):
    clim = False
    N1 = datetime(y1, 1, 1)
    N2 = datetime(y2, 1, 1)
    
    return list(subset_range(N1, N2, clim, n))

# New realm added
def eg1():
    return make_eg(variable=['tas', 'pr', 'rsus'], ensemble=emember_range(3))
def eg2():
    for r in make_eg(variable=['tas'], realm=['atmos']):
        yield r
    for r in make_eg(variable=['thetao'], table=['Omon'], realm=['ocean']):
        yield r


# New variable added to realm
def eg3_1():
    return make_eg(variable=['tas', 'pr'])
def eg3_2():
    return make_eg(variable=['rsus'])

# New files added to variable
def eg4_1():
    return make_eg(variable=['tas'], subset=make_subset()[:3])
def eg4_2():
    return make_eg(variable=['tas'], subset=make_subset()[3:])

# Files replaced in variable
def eg5_1():
    return make_eg(variable=['tas'])
def eg5_2():
    return make_eg(variable=['tas'], subset=make_subset()[:2])

def write_eg_file(filepath):
    if os.path.exists(filepath):
        raise Exception("test file exists: %s" % filepath)
    fh = open(filepath, 'w')
    fh.write('I am %s\n' % op.basename(filepath))
    fh.close()


def write_eg(prefix, seq):
    """
    Create a test directory tree under prefix.
    Files are created in <prefix>/output in CMOR's
    output directory structure

    """
    trans = cmip5.make_translator(prefix, with_version=False)
    for drs in seq:
        path = trans.drs_to_filepath(drs)
        if not op.exists(op.dirname(path)):
            os.makedirs(op.dirname(path))
        else:
            if op.exists(path):
                raise RuntimeError("%s exists" % path)

        write_eg_file(path)


def write_listing(prefix, listing_file):
    """
    Create a drs-tree from a listing file
    
    """
    def it():
        for line in open(listing_file):
            line = line.strip()
            if not line or line[0] == '#':
                continue
            yield line
    write_listing_seq(prefix, it())

        
def write_listing_seq(prefix, sequence):
    """
    Create a drs-tree from a sequence.

    You can generate symbolically linked listings from real drs files with this:
    
      find $DIR_DATASET_DIR -type l -printf '%l --> %p\n' -or -type f -print

    """
    for filename in sequence:
        # Detect symbolic link indicator
        if '-->' in filename:
            link_src, link_dest = (x.strip() for x in filename.split('-->'))

            if link_src[0] == '/' or link_dest[0] == '/':
                raise Exception("Absolute path in listing!")

            # link_src is assumed to be relative to link_dest
            link_dpath = op.join(prefix, link_dest)
            if not op.exists(op.dirname(link_dpath)):
                os.makedirs(op.dirname(link_dpath))
            os.symlink(link_src, link_dpath)

        else:
            if filename[0] == '/':
                raise Exception("Absolute path in listing!")

            path = op.normpath(filename)

            filepath = op.join(prefix, filename)
            if not op.exists(op.dirname(filepath)):
                os.makedirs(op.dirname(filepath))
            write_eg_file(filepath)


def write_eg1(prefix):
    write_eg(prefix, eg1())

def write_eg2(prefix):
    write_eg(prefix, eg2())

def write_eg3_1(prefix):
    write_eg(prefix, eg3_1())
def write_eg3_2(prefix):
    write_eg(prefix, eg3_2())

def write_eg4_1(prefix):
    write_eg(prefix, eg4_1())
def write_eg4_2(prefix):
    write_eg(prefix, eg4_2())

def write_eg5_1(prefix):
    write_eg(prefix, eg5_1())
def write_eg5_2(prefix):
    write_eg(prefix, eg5_2())



def main(argv=sys.argv):
    listing_file, outdir = sys.argv[1:]

    write_listing(outdir, listing_file)

if __name__ == '__main__':
    main()
