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
from drslib.drs import CmipDRS

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
    fh = open(os.path.join(os.path.dirname(__file__), 'cmip5_test.ls'))
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

    drs2 = CmipDRS(drs, version=12)
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


def test_13():
    # Variables with clim flag as in DRS doc
    drs = translator_noversion.filename_to_drs('novar1_Amon_HadGEM2-ES_rcp45_r1i1p1_201512-204011-clim.nc')
    assert drs.subset[2] == True

def test_14():
    # Variables with clim flag as produced by CMOR
    drs = translator_noversion.filename_to_drs('novar1_Amon_HadGEM2-ES_rcp45_r1i1p1_201512-204011_clim.nc')
    assert drs.subset[2] == True

def test_15():
    drs = translator.filepath_to_drs('cmip5/output1/IPSL/IPSL-CM5A-LR/piControl/3hr/atmos/3hr/r1i1p1/v20110324/ps/ps_3hr_IPSL-CM5A-LR_piControl_r1i1p1_275001010300-279912312100.nc')
    assert drs.institute == 'IPSL'

def test_16():
    # From Estani for Bug 111
    #ds='cmip5.output1.CSIRO-QCCCE.CSIRO-Mk3-6-0.1pctCO2.day.atmos.day.r1i1p1'
    fn='pr_day_CSIRO-Mk3-6-0_1pctCO2_r1i1p1_00010101-00201231.nc'
    path='cmip5/output1/CSIRO-QCCCE/CSIRO-Mk3-6-0/1pctCO2/day/atmos/day/r1i1p1/v20110518/pr'

    fullpath = os.path.join(path, fn)
    drs = translator.filepath_to_drs(fullpath)
    #drs.product, drs.institute, drs.model =  ds.split('.')[1:4]

    calculated_path = translator.drs_to_filepath(drs)
    assert calculated_path == fullpath

def test_17():
    # From Estani for bug 112
    drs = translator.filename_to_drs('psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_1979010100-197912311800.nc')
    print translator.drs_to_file(drs)

def test_18():
    # From Estani for bug 86
    fn = 'psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_1979010100-197912311800.nc'
    drs = translator.filename_to_drs(fn)
    calculated_fn = translator.drs_to_file(drs)

    assert calculated_fn == fn

def test_19():
    # From Estani
    fn = 'clmcalipso_cf3hr_MPI-ESM-LR_amip_r1i1p1_200810221030.nc'
    drs = translator.filename_to_drs(fn)
    calculated_fn = translator.drs_to_file(drs)

    assert calculated_fn == fn

def test_20():
    # Adding seconds to a previous example
    # ...                                    YYYYMMDDHHSS
    fn = 'psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_197901010000-19791231180000.nc'
    drs = translator.filename_to_drs(fn)
    calculated_fn = translator.drs_to_file(drs)

    assert calculated_fn == fn

def test_21():
    # As reported by Ag
    fns = ['pfull_Amon_HadGEM2-ES_piControl_r1i1p1_186001-187912-clim.nc',
           'phalf_Amon_HadGEM2-ES_piControl_r1i1p1_186001-187912-clim.nc',
           ]
    for fn in fns:
        drs = translator.filename_to_drs(fn)
        calculated_fn = translator.drs_to_file(drs)
        assert calculated_fn == fn

def test_22():
    # Gridspec support
    fn = 'gridspec_ocean_fx_GFDL-ESM2G_historical_r0i0p0.nc'
    drs = translator.filename_to_drs(fn)
    calculated_fn = translator.drs_to_file(drs)

    print fn
    print calculated_fn
    
    assert calculated_fn == fn

    assert drs.frequency == 'fx'
    assert drs.table == 'fx'
    assert drs.realm == 'ocean'
    assert drs.model == 'GFDL-ESM2G'
    assert drs.experiment == 'historical'

def test_23():
    fn = 'gridspec_ocean_fx_GFDL-ESM2G_historical_r0i0p0.nc'
    drs = translator.filename_to_drs(fn)
    drs.product = 'output1'
    drs.version = 20120101

    print translator.drs_to_filepath(drs)
