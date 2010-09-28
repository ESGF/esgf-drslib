"""
This test module uses the functional test features of nose.

"""

import tempfile, os, shutil

import drslib.p_cmip5.product as p
from drslib.p_cmip5 import init
import gen_drs

from nose import with_setup

pc = None
tmpdir = None


def setup_module():
    global pc, tmpdir
    tmpdir = tempfile.mkdtemp(prefix='p_cmip5-')
    shelve_dir = os.path.join(tmpdir, 'sh')

    # Example config file is in test directory
    test_dir = os.path.dirname(__file__)
    config = os.path.join(test_dir, 'ukmo_sample.ini')

    # Shelves are regenerated each time.  This could be optimised.
    shelves = init.init(shelve_dir)

    # Create the dummy data
    dummy_list = os.path.join(test_dir, 'p_cmip5_dummy.ls')
    gen_drs.write_listing(tmpdir, dummy_list)

    pc = p.cmip5_product(mip_table_shelve=shelves['stdo_mip'],
                         template=shelves['template'],
                         stdo=shelves['stdo'],
                         config=config)


def teardown_module():
    shutil.rmtree(tmpdir)


def get_product(var, mip, expt,startyear,endyear,
                path = ''):
    path = os.path.join(tmpdir, path)
    model = 'HADCM3'
    if pc.find_product(var, mip, expt, model, path,
                       startyear=startyear,endyear=endyear):
        print var,',',mip,',',expt,startyear,endyear,':: ', pc.product, pc.reason
        return pc.product
    else:
        print 'FAILED:: ',pc.status,':: ',var,',',mip,',',expt
        assert False

def check_product(params, expect):
    assert get_product(*params) == expect

def test_product():
    """
    Generator of multiple tests.

    """
    for var in ['tas','pr','ua']:
        for mip in ['3hr', 'day']:
            if mip == '3hr':
                expect = 'output2'
            else:
                expect = 'output1'
            yield check_product, (var, mip, 'rcp45',2050, 2050), expect

path = 'tas/r2p1i1/'
path3 = 'tas/r3p1i1/'
def test1():
    assert get_product('tas', '3hr', 'rcp45', 
                       startyear=2090, endyear=2090) == 'output1'
def test2():
    assert get_product('tas', '3hr', 'piControl', 
                       startyear=2090, endyear=2090, path=path) == 'output2'
def test3():
    assert get_product('tas', '3hr', 'piControl',
                       startyear=2090, endyear=2090, path=path3 ) == 'output1'
def test4():
    assert get_product('tas', '3hr', 'historical',
                        startyear=1990, endyear=1990 ) == 'output1'
def test5():
    assert get_product('intpdiaz', 'Omon', 'rcp45',
                        startyear=2050,endyear=2050 ) == 'output1'
def test6():
    assert get_product('intpp', 'Omon', 'rcp45',
                       startyear=2050,endyear=2050 ) == 'output1'
def test7():
    # Will fail!
    assert get_product( 'sconcno3', 'aero', 'piControl', 
                        startyear=2050,endyear=2050 ) == 'output2'
def test8():
    # Will fail!
    assert get_product( 'rlu', 'cfMon', 'AMIP', 
                        startyear=2000, endyear=2000 ) == 'output2'
