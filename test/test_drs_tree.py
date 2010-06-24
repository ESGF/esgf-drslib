
import tempfile
import shutil
import os

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

    def test_3(self):
        dt = DRSTree(self.tmpdir)
        dt.discover(product='output', institute='TEST', model='HadCM3')
        
        rt = dt.realm_trees[0]
        assert rt.state == rt.STATE_INITIAL

        rt.do_version()
        assert rt.state == rt.STATE_VERSIONED
        assert len(rt.versions.keys()) == 1
        assert 1 in rt.versions.keys()

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

#!TODO: latest

#
# Test Moving from one version to another, adding a variable
#
class TestEg3(TestEg):
    __test__ = True

    def _cmor1(self):
        gen_drs.write_eg3_1(self.tmpdir)
        dt = DRSTree(self.tmpdir)
        dt.discover(product='output', institute='TEST', model='HadCM3')

        (self.rt, ) = dt.realm_trees

    def _cmor2(self):
        gen_drs.write_eg3_2(self.tmpdir)
        self.rt.deduce_state()

        
    def _exists(self, x):
        return os.path.exists(os.path.join(self.rt.realm_dir, x))
    def _listdir(self, x):
        return os.listdir(os.path.join(self.rt.realm_dir, x))



    def test_1(self):
        self._cmor1()
        self.rt.do_version()
        self._cmor2()
        self.rt.do_version()

        assert self._exists('files')
        assert self._exists('files/rsus_r1i1p1_2')
        assert not self._exists('files/rsus_r1i1p1_1')

        assert self._exists('v1/tas')
        assert self._exists('v1/pr')
        assert not self._exists('v1/rsus')
        assert self._exists('v2/rsus')

    def test_2(self):
        self._cmor1()
        self.rt.do_version()
        self._cmor2()
        self.rt.do_version()

        assert self._exists('v2/pr/r1i1p1/pr_day_HadCM3_1pctto4x_r1i1p1_2000010100-2001123114.nc')

    def test_3(self):
        self._cmor1()
        assert self.rt.state == self.rt.STATE_INITIAL
        self.rt.do_version()
        assert self.rt.state == self.rt.STATE_VERSIONED
        self._cmor2()
        assert self.rt.state == self.rt.STATE_VERSIONED_TRANS
        self.rt.do_version()
        assert self.rt.state == self.rt.STATE_VERSIONED
        
#
# Test Moving from one version to another, updating a variable
#
class TestEg4(TestEg3):
    __test__ = True

    def _cmor1(self):
        gen_drs.write_eg4_1(self.tmpdir)
        dt = DRSTree(self.tmpdir)
        dt.discover(product='output', institute='TEST', model='HadCM3')

        (self.rt, ) = dt.realm_trees

    def _cmor2(self):
        gen_drs.write_eg4_2(self.tmpdir)
        self.rt.deduce_state()

    def test_1(self):
        self._cmor1()
        self.rt.do_version()
        self._cmor2()
        self.rt.do_version()

        assert self._exists('files')
        assert self._exists('files/tas_r1i1p1_2')
        assert self._exists('v1/tas')


    def test_2(self):
        self._cmor1()
        self.rt.do_version()
        self._cmor2()
        self.rt.do_version()

        assert len(self._listdir('files/tas_r1i1p1_1')) == 3
        assert len(self._listdir('files/tas_r1i1p1_2')) == 2
        assert len(self._listdir('v1/tas/r1i1p1')) == 3
        assert len(self._listdir('v2/tas/r1i1p1')) == 5

    # Do test_3 from superclass
        

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
