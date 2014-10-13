# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from drslib.cordex import CordexFileSystem, CordexDRS
from drslib.specs import SpecsFileSystem, SpecsDRS
from drs_tree_shared import TestEg, TestListing, test_dir
from drslib.drs_tree import DRSTree
import json

import os.path as op

class TestJson(TestEg):
    __test__ = True

    def test_1(self):
        drs_fs = CordexFileSystem(self.tmpdir)
        drs_tree = DRSTree(drs_fs)
        json_obj = json.load(open(op.join(test_dir, 'cordex_1.json')))

        drs_tree.discover_incoming_fromjson(json_obj, activity='cordex')

        assert len(drs_tree.pub_trees) == 3

    def test_2(self):
        drs_fs = SpecsFileSystem(self.tmpdir)
        drs_tree = DRSTree(drs_fs)
        with open(op.join(test_dir, 'specs_cedacc.json')) as fh:
            json_obj = [json.loads(line) for line in fh]

        drs_tree.discover_incoming_fromjson(json_obj, activity='specs')
        
        # This id will not be present if realm is not correctly split on space
        drs_id = 'specs.output.IPSL.IPSL-CM5A-LR.decadal.S20130101.mon.seaIce.OImon.sic.r3i1p1'
        assert drs_id in drs_tree.pub_trees

        p = drs_tree.pub_trees.values()[0]
        p_vars = set(drs.variable for (drs_str, drs) in p._todo)

        # All DRS objects should be for the same variable
        assert len(p_vars) == 1

