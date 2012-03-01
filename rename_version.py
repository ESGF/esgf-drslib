#!/usr/bin/env python
"""
Rename a DRS version to another version number.

This operation is unsafe as it will affect the contents of a version,
however it is necessary to fix certain inconcistencies at BADC
therefore is included here for convenience.

Usage: rename_version.py <drs_root> <dataset-id> oldversion newversion

"""

import sys
import os
import os.path as op
from glob import glob
import shutil

from drslib.drs_command import main as drstool_main
from drslib.drs import DRS, path_to_drs, drs_to_path

def main(argv=sys.argv):

    #drs_root, dataset_id, old_version, new_version = argv[1:]
    #old_version = int(old_version)
    #new_version = int(new_version)

    drs_root, = argv[1:]
    for dataset_id, (old_version, new_version) in fixes:
        fix_dataset(drs_root, dataset_id, old_version, new_version)

def fix_dataset(drs_root, dataset_id, old_version, new_version):

    drs = DRS.from_dataset_id(dataset_id)
    dataset_dir = drs_to_path(drs_root, drs)

    # First run drs_tool fix what we can
    drstool_main(['drs_tool', 'fix', '-R', drs_root, dataset_id])

    # Report the status
    drstool_main(['drs_tool', 'list', '-R', drs_root, dataset_id])

    if old_version:
        if new_version:
            # Remove the destination version
            new_version_dir = op.join(dataset_dir, 'v%d' % new_version)
            if op.exists(new_version_dir):
                _safe_rmtree(new_version_dir)

            # Now rename all file/*_<version>
            rename_files(dataset_dir, old_version, new_version)

        # Remove the version directory of the old version
        old_version_dir = op.join(dataset_dir, 'v%d' % old_version)
        if op.exists(old_version_dir):
            _safe_rmtree(old_version_dir)

        # Now you must run drs_tool
        drstool_main(['drs_tool', 'fix', '-R', drs_root, dataset_id])

        # Report the status
        drstool_main(['drs_tool', 'list', '-R', drs_root, dataset_id])
    


def _safe_rmtree(directory):
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            fpath = op.join(dirpath, filename)
            if fpath[0] == '.':
                continue
            if not op.islink(fpath):
                raise RuntimeError("Directory %s is not empty" % fpath)

    shutil.rmtree(directory)

def rename_files(dataset_dir, old_version, new_version):
    for fpath in glob(op.join(dataset_dir, 'files', '*_%d' % old_version)):
        fpath_prefix, fpath_version = fpath.split('_')
        assert int(fpath_version) == old_version

        new_fpath = '%s_%d' % (fpath_prefix, new_version)

        print '%s --> %s' % (fpath, new_fpath)
        os.rename(fpath, new_fpath)

fixes = [
    ('cmip5.output1.MOHC.HadGEM2-A.amip.3hr.atmos.cf3hr.r1i1p1', (None, None)),
    ('cmip5.output1.MOHC.HadGEM2-A.amip.mon.atmos.cfOff.r1i1p1', (20111015, 20111017)),
    ('cmip5.output1.MOHC.HadGEM2-CC.piControl.day.atmos.day.r1i1p1', (20111109, 20111115)),
    ('cmip5.output1.MOHC.HadGEM2-CC.piControl.day.land.day.r1i1p1', (20111109, 20111115)),
    ('cmip5.output1.MOHC.HadGEM2-CC.piControl.day.landIce.day.r1i1p1', (20111109, 20111115)),
    ('cmip5.output1.MOHC.HadGEM2-CC.piControl.day.ocean.day.r1i1p1', (20111109, 20111115)),
    ('cmip5.output1.MOHC.HadGEM2-CC.rcp85.mon.ocnBgchem.Omon.r2i1p1', (20111120, 20111121)), # !
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.day.atmos.day.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.day.ocean.day.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.mon.aerosol.aero.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.mon.atmos.Amon.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.mon.landIce.LImon.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.mon.land.Lmon.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.mon.ocean.Omon.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.mon.ocnBgchem.Omon.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.abrupt4xCO2.mon.seaIce.OImon.r2i1p1', (20111209, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.historical.day.land.day.r1i1p1', (20110131, 20111212)),
    ('cmip5.output1.MOHC.HadGEM2-ES.historical.day.seaIce.day.r1i1p1', (20110217, 20111214)),
    ('cmip5.output1.MOHC.HadGEM2-ES.piControl.day.land.day.r1i1p1', (20110202, 20111212)), # !
    ('cmip5.output1.MOHC.HadGEM2-ES.piControl.mon.aerosol.aero.r1i1p1', (20110524, 20111216)),
    #!CHECKME -- to orphaned versions
    ('cmip5.output1.MOHC.HadGEM2-ES.piControl.mon.ocnBgchem.Omon.r1i1p1', (20110928, 20111222)),
    ('cmip5.output1.MOHC.HadGEM2-ES.piControl.mon.seaIce.OImon.r1i1p1', (20110928, 20111222)),
    ('cmip5.output1.MOHC.HadGEM2-ES.piControl.yr.ocnBgchem.Oyr.r1i1p1', (20110928, 20111222)),
    ('cmip5.output1.MOHC.HadGEM2-ES.rcp85.day.landIce.day.r1i1p1', (20110912, 20111212)),
    #!CHECKME -- latest version contains mixture of links and files
    ('cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.aerosol.aero.r1i1p1', (None, None)), # !
    #!CHECKME -- and this one
    ('cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r1i1p1', (None, None)), # !
    ('cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.atmos.Amon.r3i1p1', (None, None)),
    ('cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.landIce.LImon.r1i1p1', (20111125, 20111215)), # !
    ('cmip5.output1.MOHC.HadGEM2-ES.rcp85.mon.land.Lmon.r1i1p1', (None, None)), # !
    ('cmip5.output2.MOHC.HadGEM2-ES.abrupt4xCO2.mon.ocean.Omon.r2i1p1', (20111209, 20111212)),
    ('cmip5.output2.MOHC.HadGEM2-ES.piControl.mon.ocean.Omon.r1i1p1', ( 20110920, 20111222)),
    ('cmip5.output2.MOHC.HadGEM2-ES.piControl.yr.ocnBgchem.Oyr.r1i1p1', (20110920, 20111222)),
]    


if __name__ == '__main__':
    main()


