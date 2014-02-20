"""
Test CORDEX DRS structure.

"""

from drslib.cordex import CordexFileSystem

cordex_fs = CordexFileSystem('/CORDEX')

def test_1():
    path = '/cordex/output/AFR-44/MOHC/ECMWF-ERAINT/evaluation/r0i0p0/MOHC-HadRM3P/v1/fx/areacella/v20010101/areacella_AFR-44_ECMWF-ERAINT_evaluation_r0i0p0_MOHC-HadRM3P_v1_fx.nc'

    drs = cordex_fs.filepath_to_drs(path)
    drs.activity = 'cordex'

    assert drs.activity == 'cordex'
    assert drs.product == 'output'
    assert drs.domain == 'AFR-44'
    assert drs.institute == 'MOHC'
    assert drs.gcm_model == 'ECMWF-ERAINT'
    assert drs.experiment == 'evaluation'
    assert drs.ensemble == (0,0,0)
    assert drs.rcm_model == 'HadRM3P'
    assert drs.rcm_version == 'v1'
    assert drs.frequency == 'fx'
    assert drs.variable == 'areacella'
    assert drs.version == 20010101
    assert drs.subset == None

def test_2():
    drs_id = 'cordex.output.AFR-44.MOHC.ECMWF-ERAINT.evaluation.r0i0p0.MOHC-HadRM3P.v1.fx.areacella.v20010101'

    drs = cordex_fs.drs_cls.from_dataset_id(drs_id)

    assert drs.activity == 'cordex'
    assert drs.product == 'output'
    assert drs.domain == 'AFR-44'
    assert drs.institute == 'MOHC'
    assert drs.gcm_model == 'ECMWF-ERAINT'
    assert drs.experiment == 'evaluation'
    assert drs.ensemble == (0,0,0)
    assert drs.rcm_model == 'HadRM3P'
    assert drs.rcm_version == 'v1'
    assert drs.frequency == 'fx'
    assert drs.variable == 'areacella'
    assert drs.version == 20010101
    assert drs.subset == None

def test_3():
    filename = 'areacella_AFR-44_ECMWF-ERAINT_evaluation_r0i0p0_MOHC-HadRM3P_v1_fx.nc'

    drs = cordex_fs.filename_to_drs(filename)

    assert drs.domain == 'AFR-44'
    assert drs.gcm_model == 'ECMWF-ERAINT'
    assert drs.experiment == 'evaluation'
    assert drs.ensemble == (0,0,0)
    assert drs.rcm_model == 'HadRM3P'
    assert drs.rcm_version == 'v1'
    assert drs.frequency == 'fx'
    assert drs.variable == 'areacella'
    assert drs.subset == None

def test_4():
    filename = 'snw_AUS-44i_ECMWF-ERAINT_evaluation_r1i1p1_MOHC-HadRM3P_v1_sem_199001-199010.nc'

    drs = cordex_fs.filename_to_drs(filename)

    assert drs.domain == 'AUS-44i'
    assert drs.rcm_model == 'HadRM3P'
