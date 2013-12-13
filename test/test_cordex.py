"""
Test CORDEX DRS structure.

"""

from drslib.cordex import CordexFileSystem

cordex_fs = CordexFileSystem('/CORDEX')

def test_1():
    path = '/CORDEX/output/AFR-44/MOHC/ECMWF-ERAINT/evaluation/r0i0p0/MOHC-HadRM3P/v1/fx/areacella/v20010101/areacella_AFR-44_ECMWF-ERAINT_evaluation_r0i0p0_MOHC-HadRM3P_v1_fx.nc'

    drs = cordex_fs.filepath_to_drs(path)
    drs.activity = 'CORDEX'

    assert drs.activity == 'CORDEX'
    assert drs.product == 'output'
    assert drs.domain == 'AFR-44'
    assert drs.institute == 'MOHC'
    assert drs.gcm_model == 'ECMWF-ERAINT'
    assert drs.experiment == 'evaluation'
    assert drs.ensemble == (0,0,0)
    assert drs.rcm_model == 'MOHC-HadRM3P'
    assert drs.rcm_version == 'v1'
    assert drs.frequency == 'fx'
    assert drs.variable == 'areacella'
    assert drs.version == 20010101
    assert drs.subset == None
