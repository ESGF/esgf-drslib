# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.


from drslib.cmip5 import CMIP5FileSystem
from drslib import p_cmip5
from drslib import drs_tree
import gen_drs

import os, shutil
import metaconfig
import tempfile

LISTING = 'multi_product.ls'

config = metaconfig.get_config('drslib')
shelve_dir = config.get('p_cmip5', 'shelve-dir')

def setup_module():
    global p_cmip5, listing, tmpdir, dt

    tmpdir = tempfile.mkdtemp(prefix='drs_tree-product-')

    print 'TMPDIR  ',tmpdir
    shelves = p_cmip5.init._find_shelves(shelve_dir)

    config_file = os.path.join(os.path.dirname(__file__), 'ukmo_sample.ini')
    listing = os.path.join(os.path.dirname(__file__), LISTING)
    gen_drs.write_listing(tmpdir, listing)
    
    p_cmip5 = p_cmip5.product.cmip5_product(mip_table_shelve=shelves['stdo_mip'],
                                            template=shelves['template'],
                                            stdo=shelves['stdo'],
                                            config=config_file,
                                            not_ok_excpt=True)
    drs_fs = CMIP5FileSystem(tmpdir)
    dt = drs_tree.DRSTree(drs_fs)
    dt.set_p_cmip5(p_cmip5)


def test_product_dup():
    """
    Test scanning a set of files that are put into multiple products.

    """


    filenames = [f.strip() for f in open(listing).readlines()]
    def iter_files():
        for filename in filenames:
            yield filename, tmpdir


    dt.discover_incoming_fromfiles(iter_files())

    # There should be 2 pub-level datasets
    assert len(dt.pub_trees) == 2

    pt1, pt2 = dt.pub_trees.values()

    # They should be in separate products
    assert pt1.drs.product != pt2.drs.product

    #!NOTE: if the test fails before here it isn't really testing multi-product ingests
    #    probably the p_cmip5 algorithm has changed to put the test data into 1 product.

    # They should be disjoint
    set1 = set(x[0] for x in pt1._todo)
    set2 = set(x[0] for x in pt2._todo)
    assert set1.isdisjoint(set2)

    # Check the total number of files is right
    assert len(set1) + len(set2) == len(filenames)



def test_product_fixed():


    filenames = ['areacella_fx_IPSL-CM5A-LR_piControl_r0i0p0.nc']
    def iter_files():
        for filename in filenames:
            yield filename, tmpdir


    dt.discover_incoming_fromfiles(iter_files())


def teardown_module():
    shutil.rmtree(tmpdir)
    


