"""
This test module uses the functional test features of nose.

"""

import tempfile, os, shutil
import zipfile

import drslib.p_cmip5.product as p
from drslib.p_cmip5 import init

from nose import with_setup

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



def check_product(params, expect):
    assert do_product(*params) == expect

def test_gen():
    for var in ['tas','pr','ua']:
        for mip in ['3hr','day']:
            if var == 'ua' and mip == '3hr':
                expect = 'output2'
            else:
                expect = 'output1'
            yield check_product, (var, mip, 'rcp45', 2050, 2050, 'tmp/a_2010_2020'), expect
