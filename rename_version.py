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

    drs_root, dataset_id, old_version, new_version = argv[1:]

    old_version = int(old_version)
    new_version = int(new_version)

    drs = DRS.from_dataset_id(dataset_id)
    dataset_dir = drs_to_path(drs_root, drs)

    # First run drs_tool fix what we can
    drstool_main(['drs_tool', 'fix', '-R', drs_root, dataset_id])

    # Report the status
    drstool_main(['drs_tool', 'list', '-R', drs_root, dataset_id])

    # Remove the destination version
    new_version_dir = op.join(dataset_dir, 'v%d' % new_version)
    if op.exists(new_version_dir):
        shutil.rmtree(new_version_dir)

    # Now rename all file/*_<version>
    rename_files(dataset_dir, old_version, new_version)

    # Remove the version directory of the old version
    old_version_dir = op.join(dataset_dir, 'v%d' % old_version)
    if op.exists(old_version_dir):
        shutil.rmtree(old_version_dir)

    # Now you must run drs_tool
    drstool_main(['drs_tool', 'fix', '-R', drs_root, dataset_id])
    
    # Report the status
    drstool_main(['drs_tool', 'list', '-R', drs_root, dataset_id])
    


def rename_files(dataset_dir, old_version, new_version):
    for fpath in glob(op.join(dataset_dir, 'files', '*_%d' % old_version)):
        fpath_prefix, fpath_version = fpath.split('_')
        assert int(fpath_version) == old_version

        new_fpath = '%s_%d' % (fpath_prefix, new_version)

        print '%s --> %s' % (fpath, new_fpath)
        os.rename(fpath, new_fpath)

if __name__ == '__main__':
    main()
