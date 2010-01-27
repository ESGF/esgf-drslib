#!/usr/bin/env python
# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Translate a stream of filepaths from CMIP3 to CMIP5 syntax
"""


import sys, os, shutil, re

import logging
log = logging.getLogger(__name__)

from isenes.drslib import cmip3, cmip5
from isenes.drslib.translate import TranslationError

cmip3_translator = cmip3.make_translator('')
cmip5_translator = cmip5.make_translator('')


class FileMover(object):
    def __init__(self, include, exclude, dry_run=True):
        self.dry_run = dry_run
        self.include = [re.compile(x) for x in include]
        self.exclude = [re.compile(x) for x in exclude]

    def walk_cmip3(self, base_path):
        """
        Walk through the CMIP3 archive
        @yield: (dirname, filenames) for terminal directories
        
        """
        for (dirpath, dirnames, filenames) in os.walk(base_path):

            # Store whether dirnames is empty before removing excluded
            # directories.
            is_leaf = not dirnames
            self.check_dirnames(dirpath, dirnames)

            if is_leaf:
                yield (dirpath, filenames)

            # This code won't be needed in Python 2.6 which has a followlinks
            # option to os.walk
            for dirname in dirnames:
                path = os.path.join(dirpath, dirname)
                if os.path.islink(path):
                    log.info('Following symlink %s' % path)
                    # Recursively walk the symlink
                    for t in self.walk_cmip3(path): 
                        yield t

    def check_dirnames(self, dirpath, dirnames):
        """
        Modify dirnames in place to remove directories according to
        self.include and self.exclude

        """
        log.debug('checking dirnames %s' % dirnames)
        
        
        for dirname in dirnames[:]:
            path = os.path.join(dirpath, dirname)
            delete = False

            for rexp in self.exclude:
                if rexp.match(path):
                    delete = True
            for rexp in self.include:
                if rexp.match(path):
                    delete = False

            if delete:
                log.info('Excluding directory %s' % dirname)
                dirnames.remove(dirname)

        log.debug('dirnames remaining %s' % dirnames)


    def _mkdirs(self, name, mode=511):
        log.info('mkdir -p %s' % name)
        #if not self.dry_run:
        #    os.makedirs(name)

    def _rename(self, old, new):
        log.info('mv %s %s' % (old, new))
        #if not self.dry_run:
        #    os.rename(old, new)

    def move_files(self, cmip3_path, cmip5_path):
        cmip3_t = cmip3.make_translator(cmip3_path)
        cmip5_t = cmip5.make_translator(cmip5_path)

        log.info('Dry run is %s' % self.dry_run)

        for dirpath, filenames in self.walk_cmip3(cmip3_path):
            log.info('Processing directory %s' % dirpath)

            try:
                drs = cmip3_t.path_to_drs(dirpath)
                path = cmip5_t.drs_to_path(drs)
            except TranslationError, e:
                log.error('Failed to translate path %s: %s' % (dirpath, e))
                continue
            except:
                log.exception('Error translating path %s' % dirpath)
                continue

            log.info('Moving atomic dataset %s' % drs)

            if not os.path.exists(path):
                self._mkdirs(path)

            for filename in filenames:
                ext = os.path.splitext(filename)[1]

                try:
                    drs2 = cmip3_t.filepath_to_drs(os.path.join(dirpath, filename))
                    filename2 = cmip5_t.drs_to_file(drs2)
                except TranslationError, e:
                    log.error('Failed to translate filename %s: %s' % (filename, e))
                    continue

                # Sanity check
                path2 = cmip5_t.drs_to_path(drs2)
                assert path2 == path

                self._rename(os.path.join(dirpath, filename),
                             os.path.join(path, filename2))

def main_old():
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

def main(args):
    from optparse import OptionParser

    usage = "usage: %prog [options] cmip3_root cmip5_root"
    parser = OptionParser(usage=usage)

    parser.add_option('-i', '--include', action='append', dest='include', default=[],
                      help='Include paths matching INCLUDE regular expression')
    parser.add_option('-e', '--exclude', action='append', dest='exclude', default=[],
                      help='Exclude paths matching EXCLUDE regular expression')

    #!TODO: --dry-run flag

    (options, args) = parser.parse_args()
    cmip3_path, cmip5_path = args

    if options.include:
        log.info('Include %s' % options.include)
    if options.exclude:
        log.info('Exclude %s' % options.exclude)

    mover = FileMover(options.include, options.exclude)
    mover.move_files(cmip3_path, cmip5_path)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    main(sys.argv[1:])
