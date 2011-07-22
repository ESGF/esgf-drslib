"""
Test drslib is configured to accept decadal experiments with explicit years rather than "decadalXXXX"

"""

from drslib import cmip5
from drslib.translate import TranslationError

cmip5_trans = None

def setup():
    global cmip5_trans

    cmip5_trans = cmip5.make_translator('/cmip5', with_version=False)

years = range(1960, 2010)
        

def test():
    filepat = "zg_Amon_HadCM3_decadal%s_r4i2p1_196011-199012.nc"

    for year in years:
        filename = filepat % year

        print year, 

        try:
            drs_obj = cmip5_trans.filename_to_drs(filename)
        except TranslationError:
            raise AssertionError

        assert drs_obj.experiment == 'decadal%s' % year
    
