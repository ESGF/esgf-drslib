"""
Bulk Generate DRS objects for testing.

"""

import random
from copy import copy
from itertools import product, izip
from datetime import datetime
import os

from isenes.drslib.drs import DRS
from isenes.drslib import cmip5


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
    #import pdb; pdb.set_trace()
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
        N1 = (dt1.year, dt1.month, dt1.day, dt1.hour)
        N2 = (dt2.year, dt2.month, dt2.day, dt2.hour)
        yield (N1, N2, clim)

def eg1():
    template = DRS(activity='cmip5', product='output', institute='TEST',
                   model='HadCM3', experiment='1pctto4x', 
                   frequency='day', realm='atmos', 
                   )

    variables = ['tas', 'pr', 'rsus']
    N1 = datetime(2000, 1, 1)
    N2 = datetime(2010, 1, 1)
    n = 5
    clim = False

    for t2 in iter_drs_template(template, 
                                dict(variable=variables, 
                                     ensemble=emember_range(3),
                                     subset=subset_range(N1, N2, clim, n))):
        
        yield t2
    
def write_eg1(prefix):
    """
    Create a test directory tree under prefix.

    """
    trans = cmip5.make_translator(prefix, with_version=False)
    for drs in eg1():
        path = trans.drs_to_filepath(drs)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        else:
            if os.path.exists(path):
                raise RuntimeError("%s exists" % path)

        fh = open(path,'w')
        fh.write('I am %s\n' % os.path.basename(path))
        fh.close()
