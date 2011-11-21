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

from drs_tree_shared import TestEg
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
            assert self.pt.state != self.pt.STATE_BROKEN
            
        

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

