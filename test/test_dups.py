"""
Test detection of duplicates in drs_tree.

"""

import os

from unittest import TestCase
import shutil
import tempfile

import gen_drs
from drslib.drs_tree import DRSTree
from drs_tree_shared import TestEg, test_dir

CHANGE_FILE = 'hfss_Amon_HadGEM2-ES_rcp45_r1i1p1_209012-209911.nc'


class TestDups(TestEg):
    def setUp(self):
        super(TestDups, self).setup()

        # Create test data
        gen_drs.write_eg1(self.tmpdir)

        # Do initial version change
        self.dt = DRSTree(self.tmpdir)
        self.dt.discover(self.incoming, activity='cmip5',
                         product='output1', institute='MOHC', model='HadCM3')
        self.pt = dt.pub_trees.values()[0]
        self.pt.do_version()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _make_incoming1(self):
        # Original ingest
        gen_drs.write_listing(self.incoming, os.path.join(test_dir, 'dups1.ls'))

    def _make_incoming2(self):
        # Ingest with some new files and 2 duplicates
        gen_drs.write_listing(self.incoming, os.path.join(test_dir, 'dups2.ls'))
        
    def _make_incoming3(self):
        # As incoming2 except one of the dups differs in size
        self._make_incoming2()

        fh = open(os.path.join(self.incoming, CHANGE_FILE), 'a')
        print >>fh, 'File has grown'

    def _make_incoming4(self):
        # As incoming2 except one of the dups only differs by contents
        self._make_incoming2()

        fh = open(os.path.join(self.incoming, CHANGE_FILE), 'r+')
        fh.seek(0)
        fh.write('XXX')
        fh.close()

    #!TODO: test tracking_id detection with a real NetCDF file.
