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
shelve_dir = None

def setup_module():
    global pc1, pc2, tmpdir, shelve_dir
    tmpdir = tempfile.mkdtemp(prefix='p_cmip5-')
    print 'TMPDIR   ',tmpdir
    shelve_dir = os.path.join(tmpdir, 'sh')

    # Example config file is in test directory
    test_dir = os.path.dirname(__file__)
    config1 = os.path.join(test_dir, 'sample_1.ini')
    config2 = os.path.join(test_dir, 'sample_2.ini')

    # Shelves are regenerated each time.  This could be optimised.
    init.init(shelve_dir)
    shelves = init._find_shelves(shelve_dir)

    # Create the dummy data
    z = zipfile.ZipFile(os.path.join(test_dir, 'dummy_archive.zip'))
    z.extractall(path=tmpdir)

    pc1 = p.cmip5_product(mip_table_shelve=shelves['stdo_mip'],
                          template=shelves['template'],
                          stdo=shelves['stdo'],
                          config=config1, not_ok_excpt=False)
    pc2 = p.cmip5_product(mip_table_shelve=shelves['stdo_mip'],
                          template=shelves['template'],
                          stdo=shelves['stdo'],
                          config=config2, not_ok_excpt=False)


##def teardown_module():
    ##shutil.rmtree(tmpdir)




def do_product2(var, mip, expt,path, startyear,
            pci=None,path_output1=None,path_output2=None,verbose=False, tab='    '):
    model = 'HADCM3'

    path = os.path.join(tmpdir, path)
    if path_output1 != None:
      path_output1 = os.path.join(tmpdir, path_output1)
    if pci is None:
        pci = pc1

    if startyear == None and False:
        if pci.find_product_ads( var, mip, expt,model,path, verbose=verbose):
            #print tab,var,',',mip,',',expt,path,':: ',pci.product, pci.reason 
            if pci.product == 'split':
                if len( pci.output1_files ) == 0:
                    print tab,' ***** NO FILES FOUND'
                    assert False
                else:
                    pass
                    ##print tab,'    --> output1: %s .... %s' % (pci.output1_files[0],pci.output1_files[-1])
        else:
            print tab,'FAILED:: ',pci.reason,':: ',var,',',mip,',',expt
    else:
        if path_output1 != None:
           print 'PATH_OUTPUT1:: ',path_output1
        pci.find_product( var, mip, expt,model,path,startyear=startyear,path_output1=path_output1,path_output2=path_output2, verbose=verbose)

    return (pci.product, pci.rc)

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
            print tab,'FAILED:: ',pci.reason,':: ',var,',',mip,',',expt
    else:
        if pci.find_product( var, mip, expt,model,path,startyear=startyear, verbose=verbose):
            print tab,var,',',mip,',',expt,path,startyear,':: ',pci.product, pci.reason 
        else:
            print tab,'FAILED:: ',pci.reason,':: ',var,',',mip,',',expt

    return (pci.product, pci.rc)



def check_product(args, kwargs, expect=None):
    r = do_product(*args, **kwargs)
    if expect:
        assert r[0] == expect, '%s :: %s' % (str(r),str(expect))

def check_product2(args, expect=None):
    r = do_product2(*args)
    if expect:
        assert r == expect, '%s :: %s' % (str(r),str(expect))

def check_product3(args, kwargs, expect=None):
    r = do_product2(*args, **kwargs)
    if expect:
        assert r == expect, '%s :: %s' % (str(r),str(expect))

def test_gen():
    for var in ['tas','pr','ua']:
        for mip in ['3hr','day']:
            if mip == '3hr':
                expect = 'output2'
            else:
                expect = 'output1'
            yield check_product, (var, mip, 'rcp45'), dict(startyear=2050, endyear=2050, path='tmp/a_2005_2100'), expect


def test_gen2():
    yield  check_product, ('tas', '3hr', 'rcp45'), dict(startyear=2090, endyear=2090, path='tmp/a_2010_2020', verbose=True) 
    yield  check_product, ('tas', '3hr', 'rcp60'), dict(startyear=2090, endyear=2090, path='tmp/a_2010_2020', verbose=True) 

def test_gen3():
    print '3d aero field'
    yield check_product, ( 'sconcdust', 'aero', 'rcp85'), dict(startyear=2015, path='tmp/a_2010_2020', verbose=True ), 'output2'
    yield check_product, ( 'rhs', 'day', 'historical'), dict(path='tmp/a_2005_2100', verbose=verbose ), 'split'
    yield check_product, ( 'rhs', 'day', 'historicalxxx'), dict(path='tmp/a_2005_2100', verbose=verbose ), 'output1'
    yield check_product, ( 'rhs', 'day', 'historical'), dict(path='tmp/a_1930_2000', verbose=verbose ), 'split'
    yield check_product, ( 'rhs', 'day', 'historical'), dict(path='tmp/a_1930_2000', verbose=verbose, pci=pc2 ), 'split'
    yield check_product, ( 'rhs', 'day', 'piControl'), dict(path='tmp/a_1930_2000', verbose=verbose ), 'split'

def test_gen4():
    print 'test using sample_2.ini, in which there is a 30 year offset between dating in historical and piControl'
    yield check_product, ( 'rhs', 'day', 'piControl'), dict(path='tmp/a_1930_2000', verbose=verbose, pci=pc2 ), 'split'
    yield check_product, ( 'tas', '3hr', 'piControl'), dict(path='tmp/a_2005_2100'), 'split'
    yield check_product, ( 'tas', '3hr', 'historical'), dict(startyear=1990, endyear=1990, path='tmp/a_1930_2000' ), 'output1'
    yield check_product, ( 'tasxx', '3hr', 'rcp45'), dict(startyear=2090, endyear=2090 ), 'output2'
    yield check_product, ( 'intpdiaz', 'Omon', 'rcp45'), dict(startyear=2050,endyear=2050, path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'intpp', 'Omon', 'rcp45'), dict(startyear=2050,endyear=2050, path='tmp/a_2010_2020' ), 'output1'
    yield check_product, ( 'sconcno3', 'aero', 'piControl'), dict(startyear=2050,endyear=2050, path='tmp/a_2010_2020' ), 'output1'
    yield check_product3, ( 'ta', '6hrPlev', 'midHolocene', 'tmp/a_1001_1050', 1040 ), {}, ('output1','OK200.01')
    yield check_product3, ( 'ta', '6hrPlev', 'midHolocene', 'tmp/a_1001_1050', 1040 ), {'path_output1':'tmp/a_1001_1030'}, ('Failed','ERR007')
    yield check_product, ( 'ta', '6hrPlev', 'midHolocene'), dict(path='tmp/a_2005_2100' ), 'split'
    yield check_product, ( 'emioa', 'aero', 'decadal2005'), dict(path='tmp/a_2005_2100' ), 'output1'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2005'), dict(path='tmp/a_2005_2100' ), 'split'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2005'), dict(startyear=2010, path='tmp/a_2005_2100' ), 'output2'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2005'), dict(startyear=2015, path='tmp/a_2005_2100' ), 'output1'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2005'), dict(startyear=2045, path='tmp/a_2005_2100' ), 'output2'
    yield check_product, ( 'sconcnh4', 'aero', 'decadal2001'), dict(path='tmp/a_2005_2100' ), 'split'

def test_gen5():
    print 'cfMon, section 1'
    yield check_product3, ( 'rlu', 'cfMon', 'amip', 'tmp/a_1930_2000', 1990 ), {}, ('output1','OK300')
    yield check_product3, ( 'rlu', 'cfMon', 'amip', 'tmp/single', None ), {}, ('output1','OK012')

def test_gen6():
    print 'cfMon, section 2'
    yield check_product3, ( 'rlut4co2', 'cfMon', 'piControl', 'tmp/a_1930_2000', 1950 ), {}, ('output1','OK100')

def test_gen7():
    print 'cfMon, section 3'
    yield check_product3, ( 'rlu4co2', 'cfMon', 'amip', 'tmp/a_1930_2000', 1980 ), {}, ('output1','OK300')
    yield check_product3, ( 'rlu4co2', 'cfMon', 'piControl', 'tmp/a_1930_2000', 1950  ), {}, ('output1','OK008.2')

def test_gen8():
    print '------------ cfMon, section 4 --------------'
    yield check_product3, ( 'clisccp', 'cfMon', 'amip', 'tmp/a_1930_2000', 1980 ), {}, ('output1', 'OK300')
    yield check_product3, ( 'clisccp', 'cfMon', 'piControl', 'tmp/a_2005_2100', 2020 ), {}, ('output1', 'OK200')
    yield check_product3, ( 'clisccp', 'cfMon', 'piControl', 'tmp/a_2005_2100', 2040 ), {}, ('output2', 'OK200')
    yield check_product3, ( 'clisccp', 'cfMon', 'abrupt4xco2', 'tmp/a_2010_2020', 2015 ), {}, ('output1','OK009.2')

##( 'rlu4co2', 'cfMon', 'piControl', startyear=2000, endyear=2000, path='./tmp/a_2010_2020', expected=('output1', 'OK008.2') )


def test_drs_tree():
    """
    Test drs_tree interface to p_cmip5.
    """
    from drslib import drs_tree

    # Point drs_root at /tmp since we won't be making any upgrades.
    dt = drs_tree.DRSTree('/tmp')
    dt.set_p_cmip5(pc1)
    dt.discover(os.path.join(tmpdir, 'tmp/tas'), activity='cmip5', institute='UKMO')

    #!TODO: More robust test here.
    datasets = set(dt.pub_trees.keys())
    assert datasets == set("""
cmip5.output2.UKMO.HADCM3.piControl.3hr.atmos.3hr.r1i1p1
cmip5.output2.UKMO.HADCM3.piControl.3hr.atmos.3hr.r2i1p1
cmip5.output1.UKMO.HADCM3.piControl.3hr.atmos.3hr.r1i1p1
cmip5.output1.UKMO.HADCM3.piControl.day.atmos.day.r3i1p1
cmip5.output1.UKMO.HADCM3.piControl.3hr.atmos.3hr.r2i1p1
""".strip().split())


def test_p_cmip5_data_perms():
    """
    Regression test to detect the case when the shelve files
    are only readable by the user.

    """
    global pc1

    #!TODO: Repeating bits of setup_module() here.  Could be DRY.
    test_dir = os.path.dirname(__file__)
    config1 = os.path.join(test_dir, 'sample_1.ini')
    shelves = init._find_shelves(shelve_dir)
    shelve_file = shelves['stdo']

    try:
        os.chmod(shelve_file, 0400)
        # Reload shelves
        pc1 = p.cmip5_product(mip_table_shelve=shelves['stdo_mip'],
                              template=shelves['template'],
                              stdo=shelves['stdo'],
                              config=config1, not_ok_excpt=False)
        # Repeat test
        test_drs_tree()
    finally:
        os.chmod(shelve_file, 0644)
        pc1 = p.cmip5_product(mip_table_shelve=shelves['stdo_mip'],
                              template=shelves['template'],
                              stdo=shelves['stdo'],
                              config=config1, not_ok_excpt=False)

if __name__ == '__main__':
    for x in test_gen8():
        print x
