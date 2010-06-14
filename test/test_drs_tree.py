
import tempfile
import shutil

import gen_drs
from isenes.drslib.drs_tree import RealmTree

def test_1():
    try:
        tmpdir = tempfile.mkdtemp(prefix='isenes_drslib')
        gen_drs.write_eg1(tmpdir)
        
        rt = RealmTree.from_path('%s/output/TEST/HadCM3/1pctto4x/day/atmos' % tmpdir)
        assert rt.versions == {}
        assert len(rt._todo) == 45
        assert rt._todo[0].variable == 'rsus'
        assert rt.state == rt.STATE_INITIAL
    finally:
        shutil.rmtree(tmpdir)
