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


import sys, os, re

import logging
log = logging.getLogger(__name__)

from drslib import cmip3, cmip5
from drslib.translate import TranslationError

cmip3_translator = cmip3.make_translator('')
cmip5_translator = cmip5.make_translator('')

# Redefined in main
include = None
exclude = None
dry_run = True
copy_trans = False
 
def walk_cmip3(base_path):
    """
    Walk through the CMIP3 archive
    @yield: (dirname, filenames) for terminal directories

    """
    for (dirpath, dirnames, filenames) in os.walk(base_path):

        # Store whether dirnames is empty before removing excluded
        # directories.
        is_leaf = not dirnames
        check_dirnames(dirpath, dirnames)

        if is_leaf:
            yield (dirpath, filenames)

        # This code won't be needed in Python 2.6 which has a followlinks
        # option to os.walk
        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            if os.path.islink(path):
                log.info('Following symlink %s' % path)
                # Recursively walk the symlink
                for t in walk_cmip3(path): 
                    yield t

def check_dirnames(dirpath, dirnames):
    """
    Modify dirnames in place to remove directories according to
    include and exclude

    """
    log.debug('checking dirnames %s' % dirnames)


    for dirname in dirnames[:]:
        path = os.path.join(dirpath, dirname)
        delete = False

        for rexp in exclude:
            if rexp.match(path):
                delete = True
        for rexp in include:
            if rexp.match(path):
                delete = False

        if delete:
            log.info('Excluding directory %s' % dirname)
            dirnames.remove(dirname)

    log.debug('dirnames remaining %s' % dirnames)


def _mkdirs(name, mode=0777):
    log.info('mkdir -p %s' % name)
    if not dry_run:
        os.makedirs(name, mode)

def _copy(old, new):
    cmd = 'cp %s %s' % (old, new)
    log.info(cmd)
    if not dry_run:
        os.system(cmd)

def _rename(old, new):
    cmd = 'mv %s %s' % (old, new)
    log.info(cmd)
    if not dry_run:
        os.system(cmd)

             

def trans_files(cmip3_path, cmip5_path):
    cmip3_t = cmip3.make_translator(cmip3_path)
    cmip5_t = cmip5.make_translator(cmip5_path)

    log.info('Dry run is %s' % dry_run)
    log.info('Copying is %s' % copy_trans)

    for dirpath, filenames in walk_cmip3(cmip3_path):
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

        log.info('Translating atomic dataset %s' % drs)

        if not os.path.exists(path):
            _mkdirs(path)

        for filename in filenames:

            try:
                drs2 = cmip3_t.filepath_to_drs(os.path.join(dirpath, filename))
                filename2 = cmip5_t.drs_to_file(drs2)
            except TranslationError, e:
                log.error('Failed to translate filename %s: %s' % (filename, e))
                continue

            # Sanity check
            path2 = cmip5_t.drs_to_path(drs2)
            assert path2 == path

            if copy_trans:
                _copy(os.path.join(dirpath, filename),
                      os.path.join(path, filename2))
            else:
                _rename(os.path.join(dirpath, filename),
                        os.path.join(path, filename2))

    log.info('Translation complete')


def main(argv=sys.argv):
    from optparse import OptionParser

    usage = "usage: %prog [options] cmip3_root cmip5_root"
    parser = OptionParser(usage=usage)

    parser.add_option('-i', '--include', action='append', dest='include', 
                      default=[], 
                      help='Include paths matching INCLUDE regular expression')
    parser.add_option('-e', '--exclude', action='append', dest='exclude', 
                      default=[],
                      help='Exclude paths matching EXCLUDE regular expression')

    parser.add_option('-c', '--copy', dest='copy', action='store_true', 
                     default=False,
                     help='Copy rather than move files')

    parser.add_option('-d', '--dryrun', dest='dryrun', action='store_true', 
                      default=False, 
                      help="Emit log messages but don't translate anything")

    parser.add_option('-l', '--loglevel', dest='loglevel', action='store', 
                      default='INFO',
                      help="Set logging level")

    (options, args) = parser.parse_args()
    cmip3_path, cmip5_path = args

    loglevel = getattr(logging, options.loglevel)    
    logging.basicConfig(level=loglevel,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    log.info('Calling with arguments %s' % sys.argv[1:])

    if options.include:
        log.info('Include %s' % options.include)
    if options.exclude:
        log.info('Exclude %s' % options.exclude)


    # Set global variables
    global include, exclude, dry_run, copy_trans
    include = [re.compile(x) for x in options.include]
    exclude = [re.compile(x) for x in options.exclude]
    dry_run = options.dryrun
    copy_trans = options.copy

    trans_files(cmip3_path, cmip5_path)


if __name__ == '__main__':

    main(sys.argv)
