# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.


import tempfile
import shutil
import sys, os
from glob import glob
from StringIO import StringIO
import datetime

from unittest import TestCase

import gen_drs
from drslib.drs_tree import DRSTree
from drslib.drs import path_to_drs, drs_to_path, DRS
from drslib import config

from drs_tree_shared import TestEg, TestListing

class TestEg1(TestEg):
    __test__ = True

    def setUp(self):
        super(TestEg1, self).setUp()

        gen_drs.write_eg1(self.tmpdir)

    def test_1(self):
        dt = DRSTree(self.tmpdir)
        dt.discover(self.incoming, activity='cmip5',
                    product='output1', institute='MOHC', model='HadCM3', 
                    experiment='1pctto4x', realm='atmos')
        assert len(dt.pub_trees) == 3
        k = sorted(dt.pub_trees.keys())[2]
        assert k == 'cmip5.output1.MOHC.HadCM3.1pctto4x.day.atmos.day.r3i1p1'
        pt = dt.pub_trees[k]

        assert pt.versions == {}
        assert len(pt._todo) == 15
        vars = set(x[1].variable for x in pt._todo)
        assert vars == set(('pr', 'rsus', 'tas'))
        assert pt.state == pt.STATE_INITIAL
    
    def test_2(self):
        dt = DRSTree(self.tmpdir)
        dt.discover(self.incoming, activity='cmip5',
                    product='output1', institute='MOHC', model='HadCM3')

        assert len(dt.pub_trees) == 3
        pt = dt.pub_trees.values()[0]
        assert pt.drs.realm == 'atmos'

    def test_3(self):
        dt = DRSTree(self.tmpdir)
        dt.discover(self.incoming, activity='cmip5',
                    product='output1', institute='MOHC', model='HadCM3')
        
        pt = dt.pub_trees.values()[0]
        assert pt.state == pt.STATE_INITIAL

        pt.do_version()
        assert pt.state == pt.STATE_VERSIONED
        assert len(pt.versions.keys()) == 1

        assert self.today in pt.versions.keys()

class TestEg2(TestEg):
    __test__ = True

    def setUp(self):
        super(TestEg2, self).setUp()

        gen_drs.write_eg2(self.tmpdir)

    def test_1(self):
        dt = DRSTree(self.tmpdir)
        dt.discover(self.incoming, activity='cmip5',
                    product='output1', institute='MOHC', model='HadCM3')

        assert len(dt.pub_trees) == 2
        assert set([x.drs.realm for x in dt.pub_trees.values()]) == set(['atmos', 'ocean'])

class TestEg2_1(TestEg2):
    __test__ = True

    def test_1(self):
        """Test incremental discovery"""
        dt = DRSTree(self.tmpdir)
        components = dict(activity='cmip5',
                          product='output1', institute='MOHC', model='HadCM3')
        # Call discover without incoming_dir
        dt.discover(None, **components)
        assert len(dt.pub_trees) == 0

        # Discover ocean realm
        dt.discover_incoming(self.tmpdir, realm='ocean', **components)
        assert len(dt.pub_trees) == 1

        # Discover atmos realm
        dt.discover_incoming(self.tmpdir, realm='atmos', **components)
        assert len(dt.pub_trees) == 2

        assert set([x.drs.realm for x in dt.pub_trees.values()]) == set(['atmos', 'ocean'])

    def test_2(self):
        """Test incremental discovery without calling discover() first."""
        dt = DRSTree(self.tmpdir)
        components = dict(activity='cmip5',
                          product='output1', institute='MOHC', model='HadCM3')
        assert len(dt.pub_trees) == 0

        # Discover ocean realm
        dt.discover_incoming(self.tmpdir, realm='ocean', **components)
        assert len(dt.pub_trees) == 1

        # Discover atmos realm
        dt.discover_incoming(self.tmpdir, realm='atmos', **components)
        assert len(dt.pub_trees) == 2

        assert set([x.drs.realm for x in dt.pub_trees.values()]) == set(['atmos', 'ocean'])




#!TODO: latest

#
# Test Moving from one version to another, adding a variable
#
class TestEg3(TestEg):
    __test__ = True

    def _cmor1(self):
        gen_drs.write_eg3_1(self.tmpdir)
        self.dt = DRSTree(self.tmpdir)
        self.dt.discover(self.incoming, activity='cmip5',
                         product='output1', institute='MOHC', model='HadCM3')

        (self.pt, ) = self.dt.pub_trees.values()

    def _cmor2(self):
        gen_drs.write_eg3_2(self.tmpdir)
        self.dt.discover_incoming(self.incoming, activity='cmip5',
                                  product='output1')

        
    def _exists(self, x):
        return os.path.exists(os.path.join(self.pt.pub_dir, x))
    def _listdir(self, x):
        return os.listdir(os.path.join(self.pt.pub_dir, x))
    def _listlinks(self, x):
        links = glob('%s/*' % os.path.join(self.pt.pub_dir, x))
        return [os.readlink(lnk) for lnk in links if os.path.islink(lnk)]


    def test_01(self):
        self._cmor1()
        assert len(self.pt.drs_tree.incoming) > 0

        self.pt.do_version()
        assert len(self.pt.drs_tree.incoming) == 0
        assert self.pt.count_todo() == 0
        assert len(list(self.pt.list_todo())) == 0

    def test_1(self):
        self._cmor1()
        self.pt.do_version(20100101)

        self._cmor2()
        self.pt.do_version(20100102)

        assert len(self.pt.drs_tree.incoming) == 0

        assert self._exists('files')
        assert self._exists('files/rsus_20100102')
        assert not self._exists('files/rsus_20100101')

        assert self._exists('v20100101/tas')
        assert self._exists('v20100101/pr')
        assert not self._exists('v20100101/rsus')
        assert self._exists('v20100102/rsus')

    def test_2(self):
        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()
        self.pt.do_version(20100102)

        assert self._exists('v20100102/pr/pr_day_HadCM3_1pctto4x_r1i1p1_2000010100-2001123114.nc')

    def test_3(self):
        self._cmor1()
        assert self.pt.state == self.pt.STATE_INITIAL
        self.pt.do_version()
        assert self.pt.state == self.pt.STATE_VERSIONED
        self._cmor2()
        assert self.pt.state == self.pt.STATE_VERSIONED_TRANS
        self.pt.do_version()
        assert self.pt.state == self.pt.STATE_VERSIONED
    

    def test_4(self):
        # Check all links are to the "files" branch
        self._cmor1()
        self.pt.do_version()
        self._cmor2()
        self.pt.do_version()

        links = self._listlinks('v2/tas/r1i1p1')
        for link in links:
            assert '/files/' in link

    def test_5(self):
        self._cmor1()
        self.pt.do_version(20100101)

        latest = os.readlink(os.path.join(self.pt.pub_dir, 'latest'))
        assert latest == 'v20100101'

        self._cmor2()
        self.pt.do_version(20100102)

        latest = os.readlink(os.path.join(self.pt.pub_dir, 'latest'))
        assert latest == 'v20100102'


    def test_6(self):
        # Test differencing 2 versions

        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()

        v1 = []
        todo = []
        for state, path1, path2 in self.pt.diff_version(20100101):
            if state == self.pt.DIFF_V1_ONLY:
                assert not 'rsus' in path1
                v1.append(path1)
            elif state == self.pt.DIFF_V2_ONLY:
                assert 'rsus' in path2
                todo.append(path2)

        assert len(v1) == 10
        assert len(todo) == 5


class TestEg3_1(TestEg3):
    """Use a separate DRSTree instance for the upgrade to test
    TestEg3 still works in this scenario.
    """

    __test__ = True

    def _cmor2(self):
        gen_drs.write_eg3_2(self.tmpdir)
        self.dt2 = DRSTree(self.tmpdir)
        self.dt2.discover_incoming(self.incoming, activity='cmip5',
                                  product='output1')
        (self.pt, ) = self.dt2.pub_trees.values()



#
# Test Moving from one version to another, updating a variable
#
class TestEg4(TestEg3):
    __test__ = True

    def _cmor1(self):
        gen_drs.write_eg4_1(self.tmpdir)
        self.dt = DRSTree(self.tmpdir)
        self.dt.discover(self.incoming, activity='cmip5',
                         product='output1', institute='MOHC', model='HadCM3')

        (self.pt, ) = self.dt.pub_trees.values()

    def _cmor2(self):
        gen_drs.write_eg4_2(self.tmpdir)
        self.dt.discover_incoming(self.incoming, activity='cmip5',
                                  product='output1')

    def test_1(self):
        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()
        self.pt.do_version(20100102)

        assert self._exists('files')
        assert self._exists('files/tas_20100102')
        assert self._exists('v20100102/tas')


    def test_2(self):
        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()
        self.pt.do_version(20100102)

        assert len(self._listdir('files/tas_20100101')) == 3
        assert len(self._listdir('files/tas_20100102')) == 2
        assert len(self._listdir('v20100101/tas')) == 3
        assert len(self._listdir('v20100102/tas')) == 5

    # Do test_3 from superclass
        
    # Do test_4 from superclass


    def test_6(self):
        # Test differencing 2 versions

        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()

        v1 = []
        todo = []
        for state, path1, path2 in self.pt.diff_version(20100101):
            if state == self.pt.DIFF_V1_ONLY:
                v1.append(path1)
            elif state == self.pt.DIFF_V2_ONLY:
                todo.append(path2)

        assert len(v1) == 3
        assert len(todo) == 2


class TestEg4_1(TestEg4):
    __test__ = True

    def _cmor2(self):
        gen_drs.write_eg4_2(self.tmpdir)
        self.dt2 = DRSTree(self.tmpdir)
        self.dt2.discover_incoming(self.incoming, activity='cmip5',
                                  product='output1')

        (self.pt, ) = self.dt2.pub_trees.values()


class TestEg5(TestEg4):
    __test__ = True

    def _cmor1(self):
        gen_drs.write_eg5_1(self.tmpdir)
        self.dt = DRSTree(self.tmpdir)
        self.dt.discover(self.incoming, activity='cmip5',
                         product='output1', institute='MOHC', model='HadCM3')

        (self.pt, ) = self.dt.pub_trees.values()

    def _cmor2(self):
        gen_drs.write_eg5_2(self.tmpdir)
        self.dt.discover_incoming(self.incoming, activity='cmip5',
                                  product='output1')

    # Do test1 from superclass

    def test_2(self):
        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()
        self.pt.do_version(20100102)

        assert len(self._listdir('files/tas_20100101')) == 5
        assert len(self._listdir('files/tas_20100102')) == 2
        assert len(self._listdir('v20100101/tas')) == 5
        assert len(self._listdir('v20100102/tas')) == 5

    # Do test_3 from superclass
        
    # Do test_4 from superclass

    def test_6(self):
        # Test differencing 2 versions

        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()

        v1 = []
        todo = []
        diff = []
        same = []
        for state, path1, path2 in self.pt.diff_version(20100101):
            if state == self.pt.DIFF_V1_ONLY:
                v1.append(path1)
            elif state == self.pt.DIFF_V2_ONLY:
                todo.append(path2)
            elif state == self.pt.DIFF_SIZE:
                diff.append(path1)
            elif state == self.pt.DIFF_NONE:
                same.append(path1)

        #!TODO: not same?  This test needs reviewing.
        assert len(v1) == 3
        assert len(same) == 2


class TestEg5_1(TestEg5):
    __test__ = True


    def _cmor2(self):
        gen_drs.write_eg5_2(self.tmpdir)
        self.dt2 = DRSTree(self.tmpdir)
        self.dt2.discover_incoming(self.incoming, activity='cmip5',
                                  product='output1')
        (self.pt, ) = self.dt2.pub_trees.values()






class TestSymlinks(TestEg):
    """
    Test that symlinks created during versioning are all relative.

    """
    __test__ = True

    def setUp(self):
        super(TestSymlinks, self).setUp()

        gen_drs.write_eg1(self.tmpdir)

    def test_1(self):
        dt = DRSTree(self.tmpdir)
        dt.discover(self.incoming, activity='cmip5',
                    product='output1', institute='MOHC', model='HadCM3')
        
        pt = dt.pub_trees.values()[0]
        assert pt.state == pt.STATE_INITIAL

        pt.do_version()

        for path, drs in pt.versions[pt.latest]:
            lnk = os.readlink(path)
            assert not os.path.isabs(lnk)


#----------------------------------------------------------------------------

def test_1():
    drs = path_to_drs('/cmip5', '/cmip5/output1')
    assert drs.product == 'output1'
    assert drs.institute == None

def test_2():
    drs = path_to_drs('/cmip5/', '/cmip5/output1/TEST/HadCM3/1pctto4x/day/atmos/day/r1i1p2/foo')
                      
    assert drs.institute == 'TEST'
    assert drs.experiment == '1pctto4x'
    assert drs.table == 'day'
    assert drs.ensemble == (1,1,2)

def test_3():
    drs = DRS(product='output1', institute='TEST')

    path = drs_to_path('/cmip5', drs)

    assert path == '/cmip5/output1/TEST/*/*/*/*/*/*'

def test_4():
    drs = DRS(product='output1', institute='TEST', ensemble=(1,2,3))

    path = drs_to_path('/cmip5/', drs)

    assert path == '/cmip5/output1/TEST/*/*/*/*/*/r1i2p3'

def test_5():
    drs = DRS(product='output1', institute='TEST', model='HadCM3',
              frequency='day')

    path = drs_to_path('/cmip5', drs)

    assert path == '/cmip5/output1/TEST/HadCM3/*/day/*/*/*'
