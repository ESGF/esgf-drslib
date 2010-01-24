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

from isenes.drslib import cmip3

translator = cmip3.make_translator('')

def test_1():
    p = 'cmip3/20c3m/atm/da/rsus/gfdl_cm2_0/run1/rsus_A2.19610101-19651231.nc'
    print translator.filepath_to_drs(p)
