"""
Test reparing of broken PublisherTree instances.

We expect filesystem data to be broken sometimes.  For instance if
data is moved to another site the files/* directories may be intact
but the symbolic links missing.

These tests will test whether drslib can detect inconsistencies and
repair them.

"""

import os
import shutil
from glob import glob

from drslib.publisher_tree import VERSIONING_FILES_DIR, VERSIONING_LATEST_DIR
from drslib.drs_tree import DRSTree

from drs_tree_shared import TestEg, test_dir
import gen_drs


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
    def setUp(self):
        TestEg.setUp(self)

        self._cmor1()
        self.pt.do_version(20100101)
        self._cmor2()
        self.pt.do_version(20100102)

        assert self.pt.state == self.pt.STATE_VERSIONED

        self.breakme()

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


class TestRepairLatestLink2(TestRepair2):
    __test__ = True

    def breakme(self):
        # Point latest at the wrong version
        v = os.path.join(self.pt.pub_dir, VERSIONING_LATEST_DIR)
        prev_version = 20100101
        prev_dir = 'v%d' % prev_version
        os.remove(v)
        os.symlink(prev_dir, v)


class TestRepairLatestLink(TestRepair):
    __test__ = True

    def breakme(self):
        v = os.path.join(self.pt.pub_dir, VERSIONING_LATEST_DIR)

        os.remove(v)

class TestRepairLatestVersion(TestRepair):
    __test__ = True
    
    def breakme(self):
        v = os.path.join(self.pt.pub_dir, 'v%d' % self.pt.latest)

        shutil.rmtree(v)

class TestRepairVersionContents(TestRepair):
    __test__ = True

    def breakme(self):
        version = self.pt.versions.keys()[0]
        variable = 'pr'

        var_dir = os.path.join(self.pt.pub_dir, 'v%d/%s' % (version, variable))

        # Delete every 3rd file
        for path in glob('%s/*.nc' % var_dir)[::3]:
            print 'REMOVING %s' % path
            os.remove(path)



class TestLsRepair(TestRepair):
    """
    Take a real example of a mult-version dataset that has no version directories,
    only files/*.

    """
    __test__ = True

    listing = 'multiversion_repair.ls'

    def setUp(self):
        super(TestRepair, self).setUp()

        gen_drs.write_listing(self.tmpdir, os.path.join(test_dir, self.listing))

        dt = DRSTree(self.tmpdir)
        dt.discover(self.incoming, activity='cmip5',
                    product='output1', institute='MOHC', model='HadGEM2-ES',
                    frequency='mon', realm='ocnBgchem')
        self.pt = dt.pub_trees.values()[0]

    def breakme(self):
        # Already setup and  broken
        pass
