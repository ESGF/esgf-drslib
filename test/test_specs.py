"""
Test SPECS DRS structure.

NOTE: this structure is not finalised!

"""

from drslib.specs import SpecsFileSystem, SpecsDRS

from drs_tree_shared import TestEg, TestListing

specs_fs = SpecsFileSystem('/specs')

def test_1():
    path = '/SPECS/output/MPI-M/MPI-ESM-LR/decadal/S19610101/day/atmos/day/pr/r1i1p1/v20010112/pr_day_MPI-ESM-LR_decadal_S19610101_r1i1p1_19610101-19701231.nc'

    drs = specs_fs.filepath_to_drs(path)
    drs.activity = 'specs'

    assert drs.activity == 'specs'
    assert drs.product == 'output'
    assert drs.institute == 'MPI-M'
    assert drs.model == 'MPI-ESM-LR'
    assert drs.experiment == 'decadal'
    assert drs.start_date[:3] == (1961, 1, 1)
    assert drs.frequency == 'day'
    assert drs.table == 'day'
    assert drs.realm == 'atmos'
    assert drs.ensemble == (1,1,1)
    assert drs.variable == 'pr'
    assert drs.version == 20010112
    assert drs.subset[0][:3] == (1961, 1, 1)
    assert drs.subset[1][:3] == (1970, 12, 31)


def test_2():
    drs_id = 'specs.output.MPI-M.MPI-ESM-LR.decadal.S19610101.day.atmos.day.pr.r1i1p1.v20010112'

    drs = specs_fs.drs_cls.from_dataset_id(drs_id)

    assert drs.activity == 'specs'
    assert drs.product == 'output'
    assert drs.institute == 'MPI-M'
    assert drs.model == 'MPI-ESM-LR'
    assert drs.experiment == 'decadal'
    assert drs.start_date[:3] == (1961, 1, 1)
    assert drs.frequency == 'day'
    assert drs.table == 'day'
    assert drs.realm == 'atmos'
    assert drs.ensemble == (1,1,1)
    assert drs.variable == 'pr'
    assert drs.version == 20010112
    assert drs.subset == None

def test_3():
    filename = 'pr_day_MPI-ESM-LR_decadal_S19610101_r1i1p1_19610101-19701231.nc'

    drs = specs_fs.filename_to_drs(filename)

    assert drs.activity == 'specs'    
    assert drs.experiment == 'decadal'
    assert drs.ensemble == (1,1,1)
    assert drs.model == 'MPI-ESM-LR'
    assert drs.start_date[:3] == (1961, 1, 1)
    assert drs.table == 'day'
    assert drs.variable == 'pr'
    assert drs.subset[0][:3] == (1961, 1, 1)
    assert drs.subset[1][:3] == (1970, 12, 31)

def test_4():
    filename = 'msftmyzba_Omon_IPSL-CM5A-LR_decadal_S19620101_r3i1p1_196201-197112.nc'

    drs = specs_fs.filename_to_drs(filename)

    assert drs.activity == 'specs'
    assert drs.variable == 'msftmyzba'
    assert drs.table == 'Omon'
    assert drs.model == 'IPSL-CM5A-LR'
    assert drs.experiment == 'decadal'
    assert drs.start_date[:3] == (1962, 1, 1)
    assert drs.ensemble == (3,1,1)
    assert drs.subset[0][:2] == (1962, 01)
    assert drs.subset[1][:2] == (1971, 12)

def test_5():
    filename = 'goro_fx_IPSL-CM5A-LR_decadal_S19820101_r0i0p0.nc'

    drs = specs_fs.filename_to_drs(filename)

    assert drs.activity == 'specs'
    assert drs.variable == 'goro'
    assert drs.table == 'fx'
    assert drs.model == 'IPSL-CM5A-LR'
    assert drs.ensemble == (0,0,0)
    assert drs.start_date[:3] == (1982, 1, 1)

class TestSpecsListing1(TestListing):
    __test__ = True

    listing_file = 'specs_1.ls'

    def setUp(self):
        super(TestSpecsListing1, self).setUp()

        # incoming is not tmpdir/output.
        self.incoming = self.tmpdir

    def _init_drs_fs(self):
        self.drs_fs = SpecsFileSystem(self.tmpdir)

    def test_1(self):
        self.dt.discover(self.incoming, activity='specs',
                         product='output',
                         realm='ocean',
                         frequency='mon',
                         institute='IPSL',
                         )

        print len(self.dt.pub_trees)
        assert len(self.dt.pub_trees) == 3


    def test_2(self):
        self.dt.discover(self.incoming, activity='specs',
                         product='output',
                         realm='ocean',
                         frequency='mon',
                         institute='IPSL',
                         )

        print len(self.dt.pub_trees)
        assert len(self.dt.pub_trees) == 3

        pt = self.dt.pub_trees.values()[0]
        self._do_version(pt)

        pt.deduce_state()
        assert len(pt.versions.values()[0]) == 1



        
