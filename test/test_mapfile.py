"""
Test mapfile generation.

"""

import os
import os.path as op
import re
import subprocess as S

from drslib.drs_tree import DRSTree

from drs_tree_shared import TestEg, test_dir
import gen_drs
from drslib.cmip5 import CMIP5FileSystem

from drslib.mapfile import calc_md5
import StringIO

class TestMapfile(TestEg):
    __test__ = True

    def setUp(self):
        super(TestMapfile, self).setUp()

        gen_drs.write_eg1(self.tmpdir)

        drs_fs = CMIP5FileSystem(self.tmpdir)
        dt = DRSTree(drs_fs)
        dt.discover(self.incoming, activity='cmip5',
                    product='output1', institute='MOHC', model='HadCM3')
        self.pt = dt.pub_trees.values()[0]
        self.pt.do_version()
        assert self.pt.state == self.pt.STATE_VERSIONED

    def test1(self):
        fh = StringIO.StringIO()
        self.pt.version_to_mapfile(self.pt.latest, fh, checksum_func=calc_md5)

        # Verify checksums match standard md5 tool
        fh.seek(0)
        for line in fh:
            ds_id, path, checksum = re.match(r'([^ ]+) \| ([^ ]+) \|.*checksum=([^ ]+)', line.strip()).groups()
            p = S.Popen('md5sum %s' % path, shell=True, stdout=S.PIPE)
            output = p.stdout.read()
            if not checksum in output:
                print 'LINE:', line.strip()
                print 'MD5: ', output.strip()
                assert False
