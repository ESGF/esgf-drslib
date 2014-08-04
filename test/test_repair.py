"""
Test reparing of broken PublisherTree instances.

We expect filesystem data to be broken sometimes.  For instance if
data is moved to another site the files/* directories may be intact
but the symbolic links missing.

These tests will test whether drslib can detect inconsistencies and
repair them.

"""

#!NOTE: These tests are deprecated as the fixes introduced further inconsistencies.
#       Now most fixes are unrepairable without an upgrade.
__test__ = False

import os
import shutil
from glob import glob

from drslib.drs_tree import DRSTree
from drslib.drs_tree_check import CheckLatest, VERSIONING_LATEST_DIR, VERSIONING_FILES_DIR

from drs_tree_shared import TestEg, test_dir
import gen_drs

import os.path as op

class TestRepair(TestEg):
    #__test__ = False

    def setUp(self):
        super(TestRepair, self).setUp()

        gen_drs.write_eg1(self.tmpdir)

        dt = DRSTree(self.tmpdir)
        dt.discover(self.incoming, activity='cmip5',
                    product='output1', institute='MOHC', model='HadCM3')
        self.pt = dt.pub_trees.values()[0]
        self.pt.do_version()
        assert self.pt.state == self.pt.STATE_VERSIONED

        self.breakme()

    def breakme(self):
        raise NotImplementedError

    def dump_tree(self):
        # Print out the filesystem to check something broke
        os.system('tree %s' % self.pt.pub_dir)

    def test_broken(self):
        self.pt.deduce_state()
        assert self.pt.state == self.pt.STATE_BROKEN

    def test_repair(self):
        self.pt.deduce_state()
        if self.pt.has_failures():
            self.pt.repair()
            if self.pt.state == self.pt.STATE_BROKEN:
                print '\n'.join(self.pt.list_failures()), '\n'
                raise AssertionError()
            
# For tests that need 2 versions
class TestRepair2(TestRepair):

    genfuncs = (gen_drs.write_eg3_1, gen_drs.write_eg3_2)

    def setUp(self):
        TestEg.setUp(self)

        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()
        self.pt.do_version(20100102)

        assert self.pt.state == self.pt.STATE_VERSIONED

        self.breakme()

    def _cmor1(self):
        genfunc = self.genfuncs[0]
        genfunc(self.tmpdir)

        self.dt = DRSTree(self.tmpdir)
        self.dt.discover(self.incoming, activity='cmip5',
                         product='output1', institute='MOHC', model='HadCM3')

        (self.pt, ) = self.dt.pub_trees.values()

    def _cmor2(self):
        genfunc = self.genfuncs[1]
        genfunc(self.tmpdir)

        self.dt.discover_incoming(self.incoming, activity='cmip5',
                                  product='output1')


class TestRepairLatestLink2(TestRepair2):
    __test__ = True

    def breakme(self):
        # Point latest at the wrong version
        v = op.join(self.pt.pub_dir, VERSIONING_LATEST_DIR)
        prev_version = 20100101
        prev_dir = 'v%d' % prev_version
        os.remove(v)
        os.symlink(prev_dir, v)

class TestRepairLatestLink2_2(TestRepairLatestLink2):
    genfuncs = (gen_drs.write_eg4_1, gen_drs.write_eg4_2)

class TestRepairBadLinks(TestRepair2):
    # Test the case where symbolic links exist in the files directory
    __test__ = True

    genfuncs = (gen_drs.write_eg4_1, gen_drs.write_eg4_2)


    def breakme(self):
        # Link all files in files/tas_20100101 into files/tas_20100102
        fv1 = op.join(self.pt.pub_dir, VERSIONING_FILES_DIR, 'tas_20100101')
        fv2 = op.join(self.pt.pub_dir, VERSIONING_FILES_DIR, 'tas_20100102')

        for ncpath in glob(op.join(fv1, '*')):
            src = op.relpath(ncpath, fv2)
            dest = op.join(fv2, op.basename(src))
            os.symlink(src, dest)



class TestRepairLatestLink(TestRepair):
    __test__ = True

    def breakme(self):
        v = op.join(self.pt.pub_dir, VERSIONING_LATEST_DIR)

        os.remove(v)

class TestRepairLatestVersion(TestRepair):
    __test__ = True
    
    def breakme(self):
        v = op.join(self.pt.pub_dir, 'v%d' % self.pt.latest)

        shutil.rmtree(v)

class TestRepairVersionContents(TestRepair):
    __test__ = True

    def breakme(self):
        version = self.pt.versions.keys()[0]
        variable = 'pr'

        var_dir = op.join(self.pt.pub_dir, 'v%d/%s' % (version, variable))

        # Delete every 3rd file
        for path in glob('%s/*.nc' % var_dir)[::3]:
            print 'REMOVING %s' % path
            os.remove(path)



class TestLsRepair(TestRepair):
    """
    Take a real example of a mult-version dataset that has no version directories,
    only files/*.

    """
    listing = NotImplemented
    drs_components = {}

    def setUp(self):
        super(TestRepair, self).setUp()

        gen_drs.write_listing(self.tmpdir, op.join(test_dir, self.listing))

        dt = DRSTree(self.tmpdir)
        dt.discover(self.incoming, **self.drs_components)
        self.pt = dt.pub_trees.values()[0]

    def breakme(self):
        # Already setup and  broken
        pass


class TestLsRepair1(TestLsRepair):
    __test__ = True
    listing = 'multiversion_repair.ls'
    drs_components = dict(activity='cmip5',
                          product='output1', institute='MOHC', model='HadGEM2-ES',
                          frequency='mon', realm='ocnBgchem',
                          )

class TestLsRepair2(TestLsRepair):
    __test__ = True
    listing = 'cmip5.output1.MOHC.HadGEM2-ES.rcp85.day.landIce.day.r1i1p1.ls'
    drs_components = dict(activity='cmip5',
                          product='output1', institute='MOHC', model='HadGEM2-ES',
                          frequency='day', experiment='rcp85',
                          )

