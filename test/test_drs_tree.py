
import tempfile
import shutil

from unittest import TestCase

import gen_drs
from isenes.drslib.drs_tree import DRSTree, RealmTree
from isenes.drslib.drs import cmorpath_to_drs, drs_to_cmorpath, DRS

class TestEg(TestCase):
    __test__ = False

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='isenes_drslib')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

class TestEg1(TestEg):
    __test__ = True

    def setUp(self):
        super(TestEg1, self).setUp()

        gen_drs.write_eg1(self.tmpdir)

    def test_1(self):
        
        rt = RealmTree.from_path('%s/output/TEST/HadCM3/1pctto4x/day/atmos' % self.tmpdir)
        assert rt.versions == {}
        assert len(rt._todo) == 45
        assert rt._todo[0][1].variable == 'rsus'
        assert rt.state == rt.STATE_INITIAL
    
    def test_2(self):
        dt = DRSTree(self.tmpdir)
        dt.discover(product='output', institute='TEST', model='HadCM3')

        assert len(dt.realm_trees) == 1
        assert dt.realm_trees[0].drs.realm == 'atmos'

class TestEg2(TestEg):
    __test__ = True

    def setUp(self):
        super(TestEg2, self).setUp()

        gen_drs.write_eg2(self.tmpdir)

    def test_1(self):
        dt = DRSTree(self.tmpdir)
        dt.discover(product='output', institute='TEST', model='HadCM3')

        assert len(dt.realm_trees) == 2
        assert set([x.drs.realm for x in dt.realm_trees]) == set(['atmos', 'ocean'])




def test_1():
    drs = cmorpath_to_drs('/cmip5', '/cmip5/output')
    assert drs.product == 'output'
    assert drs.institute == None

def test_2():
    drs = cmorpath_to_drs('/cmip5/', '/cmip5/output/TEST/HadCM3/1pctto4x/day/atmos/foo')
                      
    assert drs.institute == 'TEST'
    assert drs.experiment == '1pctto4x'
    assert drs.variable == 'foo'

def test_3():
    drs = DRS(product='output', institute='TEST')

    path = drs_to_cmorpath('/cmip5', drs)

    assert path == '/cmip5/output/TEST'

def test_4():
    drs = DRS(product='output', institute='TEST')

    path = drs_to_cmorpath('/cmip5/', drs)

    assert path == '/cmip5/output/TEST'

def test_5():
    drs = DRS(product='output', institute='TEST', model='HadCM3',
              frequency='day')

    path = drs_to_cmorpath('/cmip5', drs)

    assert path == '/cmip5/output/TEST/HadCM3'
