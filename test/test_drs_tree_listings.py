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

import gen_drs
from drslib.drs_tree import DRSTree
from drslib.drs import path_to_drs, drs_to_path, DRS
from drslib import config

from drs_tree_shared import TestEg, TestListing

class TestListing1(TestListing):
    __test__ = True

    listing_file = 'realm_1.ls'

    def test_1(self):

        self._discover('MPI-M', 'ECHAM6-MPIOM-HR')
        pt = self.dt.pub_trees.values()[0]
        self._do_version(pt)

    def test_2(self):
        self._discover('MPI-M', 'ECHAM6-MPIOM-LR')
        pt = self.dt.pub_trees.values()[0]
        self._do_version(pt)

class TestListingOptVar(TestListing):
    __test__ = True

    listing_file = 'opt_var.ls'

    def test_1(self):
        # This should detect no pub_trees because realm was not specified
        self.dt.discover(self.incoming, activity='cmip5',
                         product='output1',
                         institute='MOHC',
                         model='HadGEM2-ES')
        assert len(self.dt.pub_trees) == 0


    def test_2(self):
        # This should accept the provided realm
        self.dt.discover(self.incoming, activity='cmip5',
                         product='output1',
                         institute='MOHC',
                         model='HadGEM2-ES',
                         realm='atmos')

        pt = self.dt.pub_trees.values()[0]
        self._do_version(pt)
        #!TODO: confirm realm set right


class TestCopyUpgrade(TestListing):
    """Test overriding the move command.
    """

    __test__ = True

    listing_file = 'realm_1.ls'

    def test_1(self):
        self._discover('MPI-M', 'ECHAM6-MPIOM-HR')
        self.dt.set_move_cmd('cp')
        
        pt = self.dt.pub_trees.values()[0]
        filename = self.dt.incoming[0][0]
        
        # Filename should remain after copy
        assert os.path.exists(filename)
        self._do_version(pt)
        assert os.path.exists(filename)
        
        # Check the filename did end up in the version
        for f, drs in pt.versions.values()[0]:
            if os.path.basename(f) == os.path.basename(filename):
                assert os.path.exists(f)
                break
        else:
            # No matching versioned file found
            assert False

class TestMapfile(TestListing):
    __test__ = True

    listing_file = 'realm_1.ls'

    def test_1(self):
        self._discover('MPI-M', 'ECHAM6-MPIOM-HR')
        pt = self.dt.pub_trees.values()[0]
        self._do_version(pt)

        # Make a mapfile
        fh = StringIO()
        pt.version_to_mapfile(self.today, fh)
        mapfile = fh.getvalue()


        print mapfile
        assert 'cmip5.output1.MPI-M.ECHAM6-MPIOM-HR.rcp45.mon.ocean.Omon.r1i1p1' in mapfile
        assert 'output1/MPI-M/ECHAM6-MPIOM-HR/rcp45/mon/ocean/Omon/r1i1p1/v%s'%self.today in mapfile


