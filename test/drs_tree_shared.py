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
from drslib import config
from drslib.cmip5 import CMIP5FileSystem

test_dir = os.path.dirname(__file__)

class TestEg(TestCase):
    __test__ = False

    today = int(datetime.date.today().strftime('%Y%m%d'))

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='drslib-')
        self.incoming = os.path.join(self.tmpdir, config.DEFAULT_INCOMING)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

class TestListing(TestEg):

    # Set the following in subclasses
    #   listing_file 

    def setUp(self):
        super(TestListing, self).setUp()

        listing_path = os.path.join(test_dir, self.listing_file)
        gen_drs.write_listing(self.tmpdir, listing_path)

        self._init_drs_fs()
        self.dt = DRSTree(self.drs_fs)

    def _init_drs_fs(self):
        self.drs_fs = CMIP5FileSystem(self.tmpdir)

    def _discover(self, institute, model):
        self.dt.discover(self.incoming, activity='cmip5',
                         product='output1', 
                         institute=institute, 
                         model=model)

    def _do_version(self, pt):
        assert pt.state == pt.STATE_INITIAL
        pt.do_version()
        assert pt.state == pt.STATE_VERSIONED
        assert pt.versions.keys() == [self.today]
