"""
This test module uses the functional test features of nose.

"""

import tempfile, os, shutil
import zipfile

import drslib.p_cmip5.product as p
from drslib.p_cmip5 import init

from nose import with_setup

verbose = False

pc1 = None
pc2 = None
tmpdir = None


def setup_module():
    global pc1, pc2, tmpdir
    tmpdir = tempfile.mkdtemp(prefix='p_cmip5-')
    shelve_dir = os.path.join(tmpdir, 'sh')

    # Example config file is in test directory
    test_dir = os.path.dirname(__file__)
    config1 = os.path.join(test_dir, 'sample_1.ini')
    config2 = os.path.join(test_dir, 'sample_2.ini')

    # Shelves are regenerated each time.  This could be optimised.
    shelves = init.init(shelve_dir)

    # Create the dummy data
    z = zipfile.ZipFile(os.path.join(test_dir, 'dummy_archive.zip'))
    z.extractall(path=tmpdir)

    pc1 = p.cmip5_product(mip_table_shelve=shelves['stdo_mip'],
                          template=shelves['template'],
                          stdo=shelves['stdo'],
                          config=config1)
    pc2 = p.cmip5_product(mip_table_shelve=shelves['stdo_mip'],
                          template=shelves['template'],
                          stdo=shelves['stdo'],
                          config=config2)


def teardown_module():
    shutil.rmtree(tmpdir)




def do_product(var, mip, expt,startyear=None,endyear=None,path = 'tmp', 
            pci=None,verbose=False, tab='    '):
    model = 'HADCM3'

    path = os.path.join(tmpdir, path)
    if pci is None:
        pci = pc1

    if startyear == None:
        if pci.find_product_ads( var, mip, expt,model,path, verbose=verbose):
            print tab,var,',',mip,',',expt,path,':: ',pci.product, pci.reason 
            if pci.product == 'split':
                if len( pci.output1_files ) == 0:
                    print tab,' ***** NO FILES FOUND'
                    assert False
                else:
                    print tab,'    --> output1: %s .... %s' % (pci.output1_files[0],pci.output1_files[-1])
        else:
            print tab,'FAILED:: ',pci.status,':: ',var,',',mip,',',expt
            assert False
    else:
        if pci.find_product( var, mip, expt,model,path,startyear=startyear, verbose=verbose):
            print tab,var,',',mip,',',expt,path,startyear,':: ',pci.product, pci.reason 
        else:
            print tab,'FAILED:: ',pci.status,':: ',var,',',mip,',',expt
            assert False
    if pci.warning != '':
        print tab, 'WARNING:: ', pci.warning

    return pci.product



def check_product(args, kwargs, expect=None):
    r = do_product(*args, **kwargs)
    if expect:
        assert r == expect

def test_gen():
    for var in ['tas','pr','ua']:
        for mip in ['3hr','day']:
            if var == 'ua' and mip == '3hr':
                expect = 'output2'
            else:
                expect = 'output1'
            yield check_product, (var, mip, 'rcp45'), dict(startyear=2050, endyear=2050, path='tmp/a_2010_2020'), expect


def test_gen2():
    yield  check_product, ('tas', '3hr', 'rcp45'), dict(startyear=2090, endyear=2090, path='tmp/a_2010_2020', verbose=True) 
    yield  check_product, ('tas', '3hr', 'rcp60'), dict(startyear=2090, endyear=2090, path='tmp/a_2010_2020', verbose=True) 

def test_gen3():
    print '3d aero field'
    yield check_product, ( 'sconcdust', 'aero', 'rcp85'), dict(startyear=2090, endyear=2090, path='tmp/a_2010_2020', verbose=True ), 'output1'
    yield check_product, ( 'rhs', 'day', 'historical'), dict(path='tmp/a_2005_2100', verbose=verbose ), 'split'
    yield check_product, ( 'rhs', 'day', 'historicalxxx'), dict(path='tmp/a_2005_2100', verbose=verbose ), 'output1'
    yield check_product, ( 'rhs', 'day', 'historical'), dict(path='tmp/a_1930_2000', verbose=verbose ), 'split'
    yield check_product, ( 'rhs', 'day', 'historical'), dict(path='tmp/a_1930_2000', verbose=verbose, pci=pc2 ), 'split'
    yield check_product, ( 'rhs', 'day', 'piControl'), dict(path='tmp/a_1930_2000', verbose=verbose ), 'split'

def test_gen4():
    print 'test using sample_2.ini, in which there is a 30 year offset between dating in historical and piControl'
    yield check_product, ( 'rhs', 'day', 'piControl'), dict(path='tmp/a_1930_2000', verbose=verbose, pci=pc2 ), 'split'
    yield check_product, ( 'tas', '3hr', 'piControl'), dict(path='tmp/a_2005_2100'), 'split'
    yield check_product, ( 'tas', '3hr', 'historical'), dict(startyear=1990, endyear=1990, path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'tasxx', '3hr', 'rcp45'), dict(startyear=2090, endyear=2090 ), 'output2'
    yield check_product, ( 'intpdiaz', 'Omon', 'rcp45'), dict(startyear=2050,endyear=2050, path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'intpp', 'Omon', 'rcp45'), dict(startyear=2050,endyear=2050, path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'sconcno3', 'aero', 'piControl'), dict(startyear=2050,endyear=2050, path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'ta', '6hrPlev', 'midHolocene'), dict(path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'ta', '6hrPlev', 'midHolocene'), dict(path='tmp/a_2005_2100' ), 'split'
    yield check_product, ( 'emioa', 'aero', 'decadal2005'), dict(path='tmp/a_2005_2100' ), 'output1'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2005'), dict(path='tmp/a_2005_2100' ), 'split'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2005'), dict(startyear=2010, path='tmp/a_2005_2100' ), 'output2'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2005'), dict(startyear=2015, path='tmp/a_2005_2100' ), 'output1'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2005'), dict(startyear=2045, path='tmp/a_2005_2100' ), 'output2'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2001'), dict(path='tmp/a_2005_2100' ), 'split'

def test_gen5():
    print 'cfMon, section 1'
    yield check_product, ( 'rlu', 'cfMon', 'amip'), dict(startyear=2000, endyear=2000, path='tmp/a_1930_2000' ), 'output1'

def test_gen6():
    print 'cfMon, section 2'
    yield check_product, ( 'rlut4co2', 'cfMon', 'amip'), dict(startyear=2000, endyear=2000, path='tmp/a_1930_2000' ), 'output1'

def test_gen7():
    print 'cfMon, section 3'
    yield check_product, ( 'rlu4co2', 'cfMon', 'amip'), dict(startyear=2000, endyear=2000, path='tmp/a_1930_2000' ), 'output1'
    yield check_product, ( 'rlu4co2', 'cfMon', 'piControl'), dict(startyear=2000, endyear=2000, path='tmp/a_2010_2020' ), 'output1'

def test_gen8():
    print 'cfMon, section 4'
    yield check_product, ( 'clisccp', 'cfMon', 'amip'), dict(startyear=2000, endyear=2000, path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'clisccp', 'cfMon', 'piControl'), dict(startyear=2000, endyear=2000, path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'clisccp', 'cfMon', 'abrupt4xco2'), dict(startyear=2000, endyear=2000, path='tmp/a_2010_2020' ), 'output1'
