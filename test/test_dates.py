"""
Test date comparisons in drs.translate.py

"""

from test import translator
from drslib.translate import drs_dates_overlap

def check_overlap(file1, file2, expect):
    drs1 = translator.filename_to_drs(file1)
    drs2 = translator.filename_to_drs(file2)

    assert drs_dates_overlap(drs1, drs2) == expect
    

tests = [
    ('psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_197901010000-19791231180000.nc', 'psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_197901010000-19791231180000.nc', True),
    ('psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_197901010000-19791231180000.nc', 'psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_19791231180001-19791231190001.nc', False),
    ('psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_197901010000-19791231180000.nc', 'psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_19791231170001-19791231190001.nc', True),
    ('psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_19790101-19791231.nc', 'psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_19791231-19800101.nc', False),
    ('psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_19790101-19791231.nc', 'psl_6hrPlev_MPI-ESM-LR_amip_r1i1p1_19790601-19800101.nc', True),
    ]
    
def test_all():
    for file1, file2, expect in tests:
        yield check_overlap, file1, file2, expect
        # Also test the reverse
        yield check_overlap, file2, file1, expect

