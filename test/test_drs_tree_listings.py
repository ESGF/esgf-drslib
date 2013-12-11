# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.


import tempfile
import shutil
import sys, os, re
from glob import glob
from StringIO import StringIO
import datetime

import gen_drs
from drslib.drs_tree import DRSTree
from drslib import config
from drslib.cmip5 import CMIP5FileSystem

from drs_tree_shared import TestEg, TestListing, test_dir



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


class TestGridspecListing(TestListing):
    __test__ = True

    listing_file = 'gridspec.ls'

    def test_1(self):
        self._discover('NOAA-GFDL', 'GFDL-ESM2G')
        assert len(self.dt.pub_trees) == 1
        drs_id, pt = self.dt.pub_trees.items()[0]
        assert drs_id == 'cmip5.output1.NOAA-GFDL.GFDL-ESM2G.historical.fx.ocean.fx.r0i0p0'

        self._do_version(pt)
        pt.deduce_state()
        assert len(pt.versions.values()[0]) == 5
        

class TestThreeway(TestEg):
    __test__ = True

    listing_files = ['threeway_1.ls', 'threeway_2.ls', 'threeway_3.ls']

    def setUp(self):
        super(TestThreeway, self).setUp()

        self.drs_fs = CMIP5FileSystem(self.tmpdir)
        self.dt = DRSTree(self.drs_fs)
        self.listing_iter = self._iterSetUpListings()

    def _iterSetUpListings(self):
        for listing_file in self.listing_files:
            listing_path = os.path.join(test_dir, listing_file)
            gen_drs.write_listing(self.tmpdir, listing_path)

            yield listing_path

    def _discover(self):
        self.dt.discover_incoming(self.incoming, activity='cmip5',
                         product='output1',
                         institute='MOHC',
                         model='HadGEM2-ES')

    def _do_version(self, pt, next_version):
        assert next_version not in pt.versions.keys()
        pt.do_version(next_version)
        assert next_version in pt.versions.keys()

    def _check_version(self, pt, version):
        for path, drs in pt.versions[version]:
            assert os.path.islink(path)
            # link is relative
            real_path = os.path.realpath(os.path.join(os.path.dirname(path),
                                                      os.readlink(path)))
            assert os.path.isfile(real_path)

            # Check variables match
            mo = re.search(r'/files/(.*?)_\d+/(.*?)_', real_path)
            assert mo.group(1) == mo.group(2)

    def test1(self):
        v = 1
        for listing_path in self.listing_iter:
            print 'Doing version %d' % v
            self._discover()
            assert len(self.dt.pub_trees) == 1
            pt = self.dt.pub_trees.values()[0]

            self._do_version(pt, v)
            self._check_version(pt, v)
            v += 1

