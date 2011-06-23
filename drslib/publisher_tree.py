# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os, sys
from glob import glob
import stat
import datetime
import re

from drslib.cmip5 import make_translator
from drslib.translate import TranslationError
from drslib.drs import DRS, path_to_drs, drs_to_path
from drslib import config, mapfile
from drslib.p_cmip5 import ProductScope

import logging
log = logging.getLogger(__name__)

#---------------------------------------------------------------------------
# DRY definitions

VERSIONING_FILES_DIR = 'files'
VERSIONING_LATEST_DIR = 'latest'

#---------------------------------------------------------------------------

class PublisherTree(object):
    """
    A directory tree at the publication level.

    :cvar STATE_INITIAL: Flag representing the initial unversioned state

    :cvar STATE_VERSIONED: Flag representing the fully versioned state
        with no unversioned files

    :cvar STATE_VERSIONED_TRANS: Flag representing the partially versioned state
        with unversioned files outstanding.

    :param latest: Integer version number of latest version or 0

    """
    #!TODO: At some point we want to check incoming files to see if they are
    #       duplicates of already versioned files.

    STATE_INITIAL = 'INITIAL'
    STATE_VERSIONED = 'VERSIONED'
    STATE_VERSIONED_TRANS = 'VERSIONED_TRANS'

    CMD_MOVE = 0
    CMD_LINK = 1
    CMD_MKDIR = 2

    DIFF_NONE = 0
    DIFF_TRACKING_ID = 1
    DIFF_SIZE = 2
    DIFF_V1_ONLY = 4
    DIFF_V2_ONLY = 8

    def __init__(self, drs, drs_tree):

        self.drs_tree = drs_tree
        self.drs = drs
        self.state = None
        self._todo = []
        self.versions = {}
        self.latest = 0
        self._vtrans = make_translator(drs_tree.drs_root)
        self._cmortrans = make_translator(drs_tree.drs_root, with_version=False)

        #!TODO: calling internal method.  Make this method public.
        ensemble = self.drs._encode_ensemble()
        self.pub_dir = os.path.join(self.drs_tree.drs_root,
                                      self.drs.product,
                                      self.drs.institute,
                                      self.drs.model,
                                      self.drs.experiment,
                                      self.drs.frequency,
                                      self.drs.realm,
                                      self.drs.table,
                                      ensemble)
        self.deduce_state()

    def deduce_state(self):
        """
        Scan the directory structure to work out what state the
        tree is in.

        """

        self._deduce_versions()
        self._deduce_todo()

        if not self.versions:
            self.state = self.STATE_INITIAL
        elif self._todo:
            self.state = self.STATE_VERSIONED_TRANS
        else:
            self.state = self.STATE_VERSIONED


    def do_version(self, next_version=None):
        """
        Move incoming files into the next version

        """

        self._setup_versioning()

        if next_version is None:
            next_version = self._next_version()

        log.info('Transfering %s to version %d' % (self.pub_dir, next_version))
        self._do_commands(self.todo_commands(next_version))
        self.deduce_state()
        self._do_latest()

    def list_todo(self, next_version=None):
        """
        Return an iterable of command descriptions in the todo list.

        Each item in the iterable is a unix command-line string of the
        form ``"mv ... ..."`` or ``"ln -s ... ..."``

        """

        if next_version is None:
            next_version = self._next_version()

        for cmd, src, dest in self.todo_commands(next_version):
            if cmd == self.CMD_MOVE:
                yield "%s %s %s" % (self.drs_tree._move_cmd, src, dest)
            elif cmd == self.CMD_LINK:
                yield "ln -s %s %s" % (src, dest)
            elif cmd == self.CMD_MKDIR:
                yield "mkdir -p %s" % (dest, )
            else:
                raise Exception("Unrecognised command type")

    def count_todo(self):
        """
        Return the number of files to be processed on next upgrade.

        """
        return len(self._todo)

    def todo_size(self):
        """
        Return the total size of files in the todo list.

        """
        count = 0
        for filename, drs in self._todo:
            count += os.stat(filename)[stat.ST_SIZE]

        return count

    def list_files(self, version=None):
        """
        Returns a list of netcdf files found under ``version`` directory.
        Where ``version`` is an integer > 0 or None to signify latest.
        """

        if version is None:
            version = self.latest
        if version == 0:
            return []

        if version not in self.versions:
            raise Exception("When searching for NetCDF files you need to provide a `version` argument as an integer or thestring 'latest'.")

        return (filepath for filepath, drs in self.versions[version])

    def count(self, version=None):
        return len(list(self.list_files(version=version)))

    def size(self, version=None):
        count = 0
        for filename in self.list_files(version=version):
            count += os.stat(filename)[stat.ST_SIZE]

        return count

    def diff_version(self, v1, v2=None, by_tracking_id=False):
        """
        Deduce the difference between two versions or between a version
        and the todo list.
        """
        
        files1 = {}
        for filepath, drs in self.versions[v1]:
            files1[os.path.basename(filepath)] = filepath

        if v2 is None:
            fl = self._todo
        else:
            fl = self.versions[v2]

        files2 = {}
        for filepath, drs in fl:
            files2[os.path.basename(filepath)] = filepath

        for file in set(files1.keys() + files2.keys()):
            if file in  files1 and file in files2:
                yield (self._diff_file(files1[file], files2[file], 
                                       by_tracking_id),
                       files1[file], files2[file])
            elif file in files1:
                yield (self.DIFF_V1_ONLY, files1[file], None)
            else:
                yield (self.DIFF_V2_ONLY, None, files2[file])


    def version_to_mapfile(self, version, fh=None):
        if fh is None:
            fh = sys.stdout

        if version not in self.versions:
            raise Exception("Version %d not present in PublisherTree %s" % (version, self.pub_dir))

        mapfile.write_mapfile(self.versions[version], fh)

    def version_drs(self, version=None):
        """
        Return a DRS object representing the PublisherTree at the given version number.
        If the version doesn't exist an exception is raised.

        """

        if version is None:
            version = self.latest
        
        # If unversioned just return the bare DRS
        if version == 0:
            return self.drs

        if version not in self.versions:
            raise Exception("Version %d not present in PublsherTree %s" % (version, self.pub_dir))

        return DRS(self.drs, version=version)

    def todo_commands(self, next_version=None):
        """
        Yield a sequence of tuples (CMD, SRS, DEST) indicating the
        files that need to be moved and linked to transfer to next version.

        CMD is one of self.CMD_MOVE, self.CMD_LINK and self.CMD_MKDIR.  
        CMD_MOVE 
          implies executing the command DRSTree._move_command to move, copy or 
          otherwise relocate the file.
        CMD_LINK 
          implies symbolically linking.
        CMD_MKDIR 
          implies creating a leaf directory DEST and all necessary intermediate 
          directories.  CMD_MKDIR commands are only yielded if the directory 
          does not exist.  SRC is None.

        """
        
        if not self._todo:
            return

        if next_version is None:
            next_version = self._next_version()
        
        done = set()
        for filepath, drs in self._todo:
            filename = os.path.basename(filepath)
            fdir = '%s_%d' % (drs.variable, next_version)
            newpath = os.path.abspath(os.path.join(self.pub_dir, VERSIONING_FILES_DIR,
                                                   fdir, filename))


            # Detect directories needing creation
            ddir_src = os.path.dirname(newpath)
            if not os.path.exists(ddir_src):
                yield self.CMD_MKDIR, None, ddir_src

            yield self.CMD_MOVE, filepath, newpath

            linkpath = os.path.abspath(os.path.join(self.pub_dir, 'v%d' % next_version,
                                                    drs.variable,
                                                    filename))
            # Detect directories needing creation
            ddir_dst = os.path.dirname(linkpath)
            if not os.path.exists(ddir_dst):
                yield self.CMD_MKDIR, None, ddir_dst
            # Make relative to source path ddir_dst
            newpath = os.path.relpath(newpath, ddir_dst)

            yield self.CMD_LINK, newpath, linkpath

            done.add(filename)

        #!TODO: Handle deleted files!

        # Now scan through previous version to find files to update
        if self.latest != 0:
            for filepath, drs in self.versions[self.latest]:
                filename = os.path.basename(filepath)
                if filename not in done:
                    # Find link target from previous version
                    prevlink = os.path.abspath(os.path.join(self.pub_dir, 'v%d' % self.latest,
                                                            drs.variable, filename))
                    pfilepath = os.path.abspath(os.path.join(os.path.dirname(prevlink),
                                                              os.readlink(prevlink)))

                    linkpath = os.path.abspath(os.path.join(self.pub_dir, 'v%d' % next_version,
                                                            drs.variable, filename))
                    
                    # Detect directories needing creation
                    ddir = os.path.dirname(linkpath)
                    if not os.path.exists(ddir):
                        yield self.CMD_MKDIR, None, ddir
                    pfilepath = os.path.relpath(pfilepath, ddir)
                    yield self.CMD_LINK, pfilepath, linkpath


    #-------------------------------------------------------------------
    
    def _do_latest(self):
        version = max(self.versions.keys())
        latest_dir = 'v%d' % version
        log.info('Setting latest to %s' % latest_dir)
        latest_lnk = os.path.join(self.pub_dir, VERSIONING_LATEST_DIR)

        if os.path.exists(latest_lnk):
            os.remove(latest_lnk)
        os.symlink(latest_dir, latest_lnk)

    
    def _do_commands(self, commands):
        for cmd, src, dest in commands:
            if cmd == self.CMD_MOVE:
                self._do_mv(src, dest)
            elif cmd == self.CMD_LINK:
                self._do_link(src, dest)
            elif cmd == self.CMD_MKDIR:
                self._do_mkdir(dest)
            else:
                raise Exception('Internal error: Unrecognised command type %s' % cmd)

    def _do_mv(self, src, dest):
        cmd = '%s %s %s' % (self.drs_tree._move_cmd, src, dest)
        if os.path.exists(dest):
            log.warn('Overwriting existing file: %s' % cmd)
        else:
            log.info(cmd)
        #!TODO: Trap output!
        status = os.system(cmd)
        if status != 0:
            log.warn('System call failed: %d' % status)

        # Remove src from incoming
        self.drs_tree.remove_incoming(src)

    def _do_link(self, src, dest):
        if os.path.exists(dest):
            log.warning('Moving symlink %s' % dest)
            os.remove(dest)

        log.info('Linking %s %s' % (src, dest))

        os.symlink(src, dest)

    def _do_mkdir(self, ddir):
        if not os.path.exists(ddir):

            log.info('Creating %s' % ddir)
            os.makedirs(ddir)
        else:
            log.warning('Directory already exists %s' % ddir)



    def _setup_versioning(self):
        """
        Do initial configuration of directory tree to support versioning.

        """
        if not os.path.exists(self.pub_dir):
            log.info("New PublisherTree being created at %s" % self.pub_dir)
            os.makedirs(self.pub_dir)

        path = os.path.join(self.pub_dir, VERSIONING_FILES_DIR)
        if not os.path.exists(path):
            log.info('Initialising %s for versioning.' % self.pub_dir)
            os.mkdir(path)

    def _next_version(self):
        if config.version_by_date:
            today = datetime.date.today()
            return int(today.strftime('%Y%m%d'))
        else:
            return self.latest+1

    def _deduce_versions(self):
        if config.version_by_date:
            return self._deduce_date_versions()
        else:
            return self._deduce_old_versions()
            
    def _deduce_date_versions(self):
        self.latest = 0
        # Bail out if pub_dir doesn't exist yet.
        if not os.path.exists(self.pub_dir):
            return
        # Detect version paths and sort by date
        for basename in os.listdir(self.pub_dir):
            if not re.match(r'v\d+$', basename):
                continue
            i = int(basename[1:])
            self.latest = max(i, self.latest)
            vpath = os.path.join(self.pub_dir, basename)
            self.versions[i] = self._make_version_list(vpath)


    def _deduce_old_versions(self):
        i = 1
        self.versions = {}
        while True:
            vpath = os.path.join(self.pub_dir, 'v%d' % i)
            if not os.path.exists(vpath):
                return
            else:
                self.latest = i

            self.versions[i] = self._make_version_list(vpath)
            i += 1
            
        
    def _make_version_list(self, vpath):
        vlist = []
        for dirpath, dirnames, filenames in os.walk(vpath,
                                                    topdown=False):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                drs = self.drs_tree._vtrans.filepath_to_drs(filepath)
                vlist.append((filepath, drs))
        return vlist

    def _deduce_todo(self):
        """
        Filter the drs_tree's incoming list to find new files in this
        PublisherTree.

        """

        FILTER_COMPONENTS = ['institution', 'model', 'experiment',
                             'frequency', 'realm', 'table',
                             'ensemble', 'product',
                             ]

        # Gather DRS components from the template drs instance to filter
        filter = {}
        for comp in FILTER_COMPONENTS:
            val = self.drs.get(comp, None)
            if val is not None:
                filter[comp] = val

        # Filter the incoming list
        if self.drs_tree.incoming:
            self._todo = self.drs_tree.incoming.select(**filter)
        else:
            self._todo = []

        log.info('Deduced %d incoming DRS files for PublisherTree %s' % 
                 (len(self._todo), self.drs))
                

    def _diff_file(self, filepath1, filepath2, by_tracking_id=False):
        diff_state = self.DIFF_NONE

        # Check files are the same size
        if _get_size(filepath1) != _get_size(filepath2):
            diff_state |= self.DIFF_SIZE

        # Check by tracking_id
        if by_tracking_id:
            if filepath1[-3:] == filepath2[-3:] == '.nc':
                if _get_tracking_id(filepath1) != _get_tracking_id(filepath2):
                    diff_state |= self.DIFF_TRACKING_ID

        #!TODO: what about md5sum?  This would be slow, particularly as
        #       esgpublish does it anyway.

        return diff_state



def _get_tracking_id(filename):
    import cdms2
    ds = cdms2.open(filename)
    return ds.tracking_id

def _get_size(filename):
    return os.stat(filename)[stat.ST_SIZE]
