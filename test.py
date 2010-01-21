"""
Tests compatible with nosetests

"""

from isenes.drslib import cmip5

translator = cmip5.CMIP5Translator('')

def get_drs1():
    return translator.filename_to_drs('tas_Amon_HadCM3_historicalNat_r1_185001-200512.nc')

def test_1():
    drs = get_drs1()

    print drs.__dict__

def test_2():
    drs = get_drs1()

    # Add the bits missing from the conversion
    drs.institute='UKMO'
    #!TODO: The translator should get this from the MIP tables
    drs.frequency = 'mon'
    drs.version = 2
    drs.product = 'output'
    #!TODO: The translator should get this from the MIP tables
    drs.realm = 'atmos'
    
    print translator.drs_to_path(drs)
