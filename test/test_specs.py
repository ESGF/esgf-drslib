"""
Test SPECS DRS structure.

NOTE: this structure is not finalised!

"""

from drslib.specs import SpecsFileSystem, SpecsDRS

from drs_tree_shared import TestEg, TestListing

specs_fs = SpecsFileSystem('/specs')

def test_1():
    path = '/SPECS/output/MPI-M/MPI-ESM-LR/decadal/series1/S19610101/day/atmos/day/pr/r1i1p1/v20010112/pr_day_MPI-ESM-LR_decadal_series1_S19610101_r1i1p1_19610101-19701231.nc'

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
    drs_id = 'specs.output.MPI-M.MPI-ESM-LR.decadal.series1.S19610101.day.atmos.day.pr.r1i1p1.v20010112'

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
    filename = 'pr_day_MPI-ESM-LR_decadal_series1_S19610101_r1i1p1_19610101-19701231.nc'

    drs = specs_fs.filename_to_drs(filename)

    assert drs.activity == 'specs'    
    assert drs.experiment == 'decadal'
    assert drs.experiment_series == 'series1'
    assert drs.ensemble == (1,1,1)
    assert drs.model == 'MPI-ESM-LR'
    assert drs.start_date == None
    assert drs.frequency == 'day'
    assert drs.variable == 'pr'
    assert drs.subset[0][:3] == (1961, 1, 1)
    assert drs.subset[1][:3] == (1970, 12, 31)



# class TestSpecsListing1(TestListing):
#     __test__ = True

#     listing_file = 'specs_test_EUR-44.ls'

#     def setUp(self):
#         super(TestSpecsListing1, self).setUp()

#         # incoming is not tmpdir/output.
#         self.incoming = self.tmpdir

#     def _init_drs_fs(self):
#         self.drs_fs = SpecsFileSystem(self.tmpdir)

#     def test_1(self):
#         self.dt.discover(self.incoming, activity='specs',
#                          product='output')

#         print len(self.dt.pub_trees)
#         assert len(self.dt.pub_trees) == 168

#     def test_2(self):
#         self.dt.discover(self.incoming, activity='specs',
#                          product='output',
#                          frequency='day')

#         print len(self.dt.pub_trees)
#         assert len(self.dt.pub_trees) == 50

#     def test_3(self):
#         self.dt.discover(self.incoming, activity='specs',
#                          product='output',
#                          frequency='day',
#                          variable='vas')

#         print len(self.dt.pub_trees)
#         assert len(self.dt.pub_trees) == 1

#         pt = self.dt.pub_trees.values()[0]
#         self._do_version(pt)




        
