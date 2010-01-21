"""
Tests compatible with nosetests

"""

from isenes.drslib import cmip5


def test_1():
    t = cmip5.CMIP5Translator('')

    drs = t.filename_to_drs('tas_Amon_HadCM3_historicalNat_r1_185001-200512.nc')
    print drs.__dict__

