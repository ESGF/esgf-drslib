# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from drslib.cordex import CordexFileSystem, CordexDRS
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
        #!TODO: json drs keys do not match internal names.  E.g. gcm_model vs driving_model, 
        #       model_version vs. rcm_version.  
        #!TODO: table is not in the json so need to look at filename too.

        assert False #!TODO
