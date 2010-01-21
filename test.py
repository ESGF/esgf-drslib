"""
Tests compatible with nosetests

"""

from isenes.drslib import cmip5

translator = cmip5.make_translator('')

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
    
    path = translator.drs_to_path(drs)

    assert path=='cmip5/output/UKMO/HadCM3/historicalNat/mon/atmos/tas/r1/v2/tas_Amon_HadCM3_historicalNat_r1_18501-200512.nc'
