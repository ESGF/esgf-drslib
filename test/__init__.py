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

from drslib import cmip5
from drslib.drs import DRS

translator = cmip5.make_translator('cmip5')
translator_noversion = cmip5.make_translator('cmip5', with_version=False)

def get_drs1():
    return translator.filename_to_drs('tas_Amon_HadCM3_historicalNat_r1i1p1_185001-200512.nc')

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

    assert path=='cmip5/output/MOHC/HadCM3/historicalNat/mon/atmos/Amon/r1i1p1/v2/tas/tas_Amon_HadCM3_historicalNat_r1i1p1_185001-200512.nc'



def roundtrip_filename(filename):
    drs = translator.filename_to_drs(filename)

    drs.version = 1
    drs.product = 'output'
    assert drs.is_complete()

    path = translator.drs_to_filepath(drs)

    assert os.path.basename(path) == filename

def test_3():
    roundtrip_filename('tas_Amon_HadCM3_historicalNat_r1i1p1_185001-200512.nc')


def test_4():
    # Read some filenames from UKMO and roundtrip them
    fh = open(os.path.join(os.path.dirname(__file__), 'cmip5_test_ls'))
    for filename in fh:
        yield roundtrip_filename, filename.strip()

def test_5():
    # Regression test for a bug
    print translator.path_to_drs('cmip5/output/MOHC/HadCM3/historicalNat/mon/atmos/Amon/r1i1p1/v3/tas/tas_Amon_HadCM3_historicalNat_r1i1p1_185001-200512.nc')

def test_6():
    # Bug reported by Ag
    print translator.filename_to_drs('cct_Amon_HadGEM2-ES_piControl_r1i1p1.nc')


def test_7():
    # Test creating path without version

    drs = get_drs1()

    # Add the bits missing from the conversion
    drs.product = 'output'
    
    path = translator_noversion.drs_to_filepath(drs)

    assert path=='cmip5/output/MOHC/HadCM3/historicalNat/mon/atmos/tas/r1i1p1/tas_Amon_HadCM3_historicalNat_r1i1p1_185001-200512.nc'

def test_8():
    # Test files created from the cmor test suite (2010-06-25)
    # This list has been adapted from the result of running "make test"
    # in cmor.  Numeric prefixes to the "hfls" variable name have been removed.
    fh = open(os.path.join(os.path.dirname(__file__), 'cmor_test_ls'))
    for filename in fh:
        yield roundtrip_filename, filename.strip()

def test_9():
    # Regression test for bug in non-versioned path construction
    
    drs = get_drs1()

    # Add the bits missing from the conversion
    drs.product = 'output'
    
    path = translator_noversion.drs_to_path(drs)

    assert path=='cmip5/output/MOHC/HadCM3/historicalNat/mon/atmos/tas/r1i1p1'

def test_10():
    # Check instantiating DRS objects from other DRS objects

    drs = get_drs1()
    assert drs.version == None

    drs2 = DRS(drs, version=12)
    assert drs2.version == 12
    assert drs.model == drs2.model

def test_11():
    # Regression test for files in multiple realms

    drs = translator_noversion.filename_to_drs('snw_LImon_HadGEM2-ES_rcp45_r1i1p1_201512-204011.nc')

    assert drs.realm == 'landIce'

def test_11():
    # Check single ensemble number is allowed
    drs = translator_noversion.filename_to_drs('hur_Amon_HadGEM2-ES_historical_r1_186212-186311.nc')
    print drs.to_dataset_id()

def test_11():
    # Detect regression where 0-indexed ensembles are printed wrong
    drs = translator_noversion.filename_to_drs('areacella_fx_IPSL-CM5A-LR_piControl_r0i0p0.nc')
    assert drs.ensemble == (0, 0, 0)
    assert 'r0i0p0' in repr(drs)


def test_12():
    # Variables not in MIP table
    drs = translator_noversion.filename_to_drs('novar1_Amon_HadGEM2-ES_rcp45_r1i1p1_201512-204011.nc')


