# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Tests compatible with nosetests

"""


import os

from isenes.drslib import cmip3, cmip5

translator = cmip3.make_translator('')
cmip5_translator = cmip5.make_translator('')

def test_1():
    p = 'cmip3/20c3m/atm/da/rsus/gfdl_cm2_0/run1/rsus_A2.19610101-19651231.nc'
    p2 = convert(p)
    assert p2 == 'cmip3/output/GFDL/CM2/20c3m/day/atmos/rsus/r1/v1/rsus_A2_CM2_20c3m_r1_19610101-19651231.nc'
    
def test_listing():
    """
    Test successful conversion of part of the CMIP3 listing
    
    """
    
    fh = open(os.path.join(os.path.dirname(__file__), 'cmip3_test_ls'))
    for line in fh:
        yield convert, line.strip()
    
def convert(filepath):
    drs = translator.filepath_to_drs(filepath)
    cmip5_filepath = cmip5_translator.drs_to_filepath(drs)

    print '%s --> %s' % (filepath, cmip5_filepath)
    
    return cmip5_filepath