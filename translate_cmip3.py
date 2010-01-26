# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Translate a stream of filepaths from CMIP3 to CMIP5 syntax
"""


import sys, os, shutil

import logging
log = logging.getLogger(__name__)

from isenes.drslib import cmip3, cmip5

cmip3_translator = cmip3.make_translator('')
cmip5_translator = cmip5.make_translator('')

def walk_cmip3(base_path):
    """
    Walk through the CMIP3 archive
    @yield: (dirname, filenames) for terminal directories
    
    """
    for (dirpath, dirnames, filenames) in os.walk(base_path):
        if not dirnames:
            yield (dirpath, filenames)

def _mkdirs(name, mode=511, dry_run=True):
    log.info('mkdir -p %s' % name)
    if not dry_run:
        os.makedirs(name)

def _rename(old, new, dry_run=True):
    log.info('mv %s %s' % (old, new))
    if not dry_run:
        os.rename(old, new)

def move_files(cmip3_path, cmip5_path, dry_run=True):
    cmip3_t = cmip3.make_translator(cmip3_path)
    cmip5_t = cmip5.make_translator(cmip5_path)

    log.info('Dry run is %s' % dry_run)
    
    for dirpath, filenames in walk_cmip3(cmip3_path):
        drs = cmip3_t.path_to_drs(dirpath)
        path = cmip5_t.drs_to_path(drs)

        log.info('Moving atomic dataset %s' % drs)

        if not os.path.exists(dirpath):
            _mkdirs(dirpath, dry_run)
        
        for filename in filenames:
            drs2 = cmip3_t.filepath_to_drs(os.path.join(dirpath, filename))
            filename2 = cmip5_t.drs_to_file(drs2)

            # Sanity check
            path2 = cmip5_t.drs_to_path(drs2)
            assert path2 == path
            
            _rename(os.path.join(dirpath, filename),
                    os.path.join(path, filename2),
                    dry_run)

def main():
    paths = set()
    for line in sys.stdin:
        filename, size = line.strip().split()
        fn = convert(filename)
        
        # Make sure no duplicate paths are created
        assert fn not in paths
        paths.add(fn)
    
def convert(filepath):
    drs = cmip3_translator.filepath_to_drs(filepath)
    cmip5_filepath = cmip5_translator.drs_to_filepath(drs)

    print '%s --> %s' % (filepath, cmip5_filepath)
    
    return cmip5_filepath

if __name__ == '__main__':
    main()