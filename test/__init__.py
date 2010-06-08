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

from isenes.drslib import cmip5

translator = cmip5.make_translator('cmip5')

def get_drs1():
    return translator.filename_to_drs('tas_Amon_HadCM3_historicalNat_r1_185001-200512.nc')

def test_1():
    """
    Demonstrate succesfully parsing a filename

    """
    drs = get_drs1()

    print drs.__dict__

def test_2():
    """
    Demonstrate successfully generating a DRS path from a filename

    """
    drs = get_drs1()

    # Add the bits missing from the conversion
    drs.version = 2
    drs.product = 'output'
    
    path = translator.drs_to_filepath(drs)

    assert path=='cmip5/output/UKMO/HadCM3/historicalNat/mon/atmos/v2/tas/r1/tas_Amon_HadCM3_historicalNat_r1_185001-200512.nc'



def roundtrip_filename(filename):
    drs = translator.filename_to_drs(filename)

    drs.version = 1
    drs.product = 'output'
    assert drs.is_complete()

    path = translator.drs_to_filepath(drs)

    assert os.path.basename(path) == filename

def test_3():
    roundtrip_filename('tas_Amon_HadCM3_historicalNat_r1_185001-200512.nc')


def test_4():
    # Read some filenames from UKMO and roundtrip them
    fh = open(os.path.join(os.path.dirname(__file__), 'cmip5_test_ls'))
    for filename in fh:
        yield roundtrip_filename, filename.strip()

def test_5():
    # Regression test for a bug
    print translator.path_to_drs('cmip5/output/UKMO/HadCM3/historicalNat/mon/atmos/v3/tas/r1/tas_Amon_HadCM3_historicalNat_r1_185001-200512.nc')

def test_6():
    # Bug reported by Ag
    print translator.filename_to_drs('cct_Amon_HadGEM2-ES_piControl_r1.nc')


def test_7():
    # Test creating path without version

    drs = get_drs1()

    # Add the bits missing from the conversion
    drs.version = 2
    drs.product = 'output'
    
    path = translator.drs_to_filepath(drs, with_version=False)

    assert path=='cmip5/output/UKMO/HadCM3/historicalNat/mon/atmos/tas/r1/tas_Amon_HadCM3_historicalNat_r1_185001-200512.nc'
