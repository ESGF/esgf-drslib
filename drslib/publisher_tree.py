# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os, sys
import stat
import datetime
import re
import itertools

from drslib.cmip5 import make_translator
from drslib.translate import TranslationError, drs_dates_overlap
from drslib import config, mapfile

import logging
log = logging.getLogger(__name__)


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
    STATE_BROKEN = 'BROKEN'

    CMD_MOVE = 0
    CMD_LINK = 1
    CMD_MKDIR = 2

    DIFF_NONE = 0
    DIFF_TRACKING_ID = 1
    DIFF_SIZE = 2
    DIFF_V1_ONLY = 4
    DIFF_V2_ONLY = 8
    DIFF_PATH = 16

    def __init__(self, drs, drs_tree):

        self.drs_tree = drs_tree
        self.drs = drs
        self.state = None
        self._todo = []
        self.versions = {}
        self.latest = 0

        from drslib.drs_tree_check import default_checkers
        self._checkers = default_checkers[:]
        self._checker_failures = []

        drs_fs = self.drs_tree.drs_fs
        self.pub_dir = drs_fs.drs_to_publication_path(self.drs)

        self.deduce_state()

    def deduce_state(self):
        """
        Scan the directory structure to work out what state the
        tree is in.

        """

        self._deduce_versions()
        self._deduce_todo()

        self._deduce_state()

    def _deduce_state(self, with_checks=True):
        """
        Internal API to state deduction assumes versions and TODO are
        already correct.
        """
        if not self.versions:
            #!FIXME: this is a hack.  there must be a better way
            # If the files directory is present assume broken rather than initial
            if os.path.exists(os.path.join(self.pub_dir, self.drs_tree.drs_fs.VERSIONING_FILES_DIR)):
                self.state = self.STATE_BROKEN
            else:                                  
                self.state = self.STATE_INITIAL
        elif self._todo:
            self.state = self.STATE_VERSIONED_TRANS
        else:
            self.state = self.STATE_VERSIONED

        if with_checks and self.state != self.STATE_INITIAL:
            if not self._check_tree():
                self.state = self.STATE_BROKEN

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
        self._deduce_state()

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


    def version_to_mapfile(self, version, fh=None, checksum_func=None):
        if fh is None:
            fh = sys.stdout

        if version not in self.versions:
            raise Exception("Version %d not present in PublisherTree %s" % (version, self.pub_dir))

        mapfile.write_mapfile(self.versions[version], fh, checksum_func)

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

        return self.drs_tree.drs_fs.drs_cls(self.drs, version=version)

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
        
        if next_version is None:
            next_version = self._next_version()
        

        done = set()
        todo_files = []
        for filepath, drs in self._todo:
            filename = os.path.basename(filepath)
            drs.version = next_version
            newpath = os.path.join(self.drs_tree.drs_fs.drs_to_realpath(drs),
                                   filename)

            # Detect directories needing creation
            ddir_src = os.path.dirname(newpath)
            if not os.path.exists(ddir_src):
                yield self.CMD_MKDIR, None, ddir_src


            yield self.CMD_MOVE, filepath, newpath
            todo_files.append((newpath, self.drs_tree.drs_fs.drs_to_linkpath(drs)))

        #!TODO: Handle deleted files!

        # Now scan through previous version to find files to update
        for command in self._link_commands(next_version, todo_files):
            # only yield commands that are required
            cmd, src, dest = command
            if os.path.exists(dest):
                continue

            yield command


    def list_failures(self):
        """
        Iterate over a descriptions of check failures.
 
        """
        for checker in self._checker_failures:
            yield '%-20s: ======== %s ========' % (checker.get_name(), checker.get_message())
            for stat, count in checker.get_stats().items():
                yield '%-20s: %30s = %d' % (checker.get_name(), stat, count)

    def has_failures(self):
        return self._checker_failures != []

    def repair(self):
        if self.has_failures():
            log.debug('BEGIN repairs')
            self._repair_tree()
            log.debug('END repairs')
            self._deduce_state(with_checks=True)

    #-------------------------------------------------------------------
    # These methods could be considered protected.  They are designed
    # for use by drs_check_tree.py

    def real_file_dir(self, drs, version=None):
        """
        Return the expected dir containing the real file represented by drs.
        """
        #!TODO: needs revisiting for CORDEX
        if version is None:
            version = drs.version
        elif drs.version is None:
            drs.version = version

        fdir = self.drs_tree.drs_fs.drs_to_storage(drs)
        return os.path.abspath(os.path.join(self.pub_dir, VERSIONING_FILES_DIR,
                                               fdir))

    def link_file_dir(self, drs, version=None):
        """
        Return the expected dir containing the link to the file represented by drs.
        """
        if version is None:
            version = drs.version
        
        return os.path.abspath(os.path.join(self.pub_dir, 'v%d' % version,
                                            drs.variable))




    def prev_versions(self, version):
        """
        Returns the versions before `version` sorted in descending order

        """
        pversions = [x for x in self.versions if x < version]
        return sorted(pversions, reverse=True)

    #-------------------------------------------------------------------
    
    def _do_latest(self):
        version = max(self.versions.keys())
        latest_dir = 'v%d' % version
        log.info('Setting latest to %s' % latest_dir)
        latest_lnk = os.path.join(self.pub_dir, self.drs_tree.drs_fs.VERSIONING_LATEST_DIR)

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


    def _link_commands(self, version, from_seq=None):
        """
        Functional replacement for part of todo_commands().  In order to
        support rebuilding symbolic links for broken datasets the links
        are deduced from the files branch.

        :param version: the version we want to create symbolic links for.
        :param from_seq: an iterable of (filepath, variable, fversion) to prepend to
            the files found on the filesystem.  Used to show links in self.todo_commands()
        :yield: as for todo_commands()

        """

        if from_seq is None:
            from_seq = []

        done = set()
        for filepath, link_dir in itertools.chain(from_seq,
                                                  self.drs_tree.drs_fs.iter_files_with_links(self.pub_dir, version)):
            filename = os.path.basename(filepath)

            if not os.path.exists(link_dir):
                yield self.CMD_MKDIR, None, link_dir

            # Make relative to dest
            dest = os.path.join(link_dir, filename)
            src = os.path.relpath(filepath, link_dir)

            yield self.CMD_LINK, src, dest
            done.add(filename)

        #!TODO: Handle deleted files!
        # Promote all files from the previous version

        #!TODO: overlap detection removed.  See tag 0.3.0a6 for old implementation.
        for prev_version in self.prev_versions(version):
            for filepath, link_dir in self.drs_tree.drs_fs.iter_files_with_links(self.pub_dir, prev_version, version):
                filename = os.path.basename(filepath)

                if filename in done:
                    continue

                if not os.path.exists(link_dir):
                    yield self.CMD_MKDIR, None, link_dir

                # Make relative to dest
                dest = os.path.join(link_dir, filename)
                src = os.path.relpath(filepath, link_dir)

                yield self.CMD_LINK, src, dest

    #-------------------------------------------------------------------------
    # Versioning internal methods

    def _setup_versioning(self):
        """
        Do initial configuration of directory tree to support versioning.

        """
        if not os.path.exists(self.pub_dir):
            log.info("New PublisherTree being created at %s" % self.pub_dir)
            os.makedirs(self.pub_dir)

        path = os.path.join(self.pub_dir, self.drs_tree.drs_fs.VERSIONING_FILES_DIR)
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
        self.versions = {}
        # Bail out if pub_dir doesn't exist yet.
        fdir = os.path.join(self.pub_dir, self.drs_tree.drs_fs.VERSIONING_FILES_DIR)
        if not os.path.exists(fdir):
            return

        # Version directories may not exist so initially deduce
        # versions from the files directory
        #!TODO: Revise for CORDEX
        versions = set()
        for d in os.listdir(fdir):
            subdrs = self.drs_tree.drs_fs.storage_to_drs(os.path.join(self.drs_tree.drs_fs.VERSIONING_FILES_DIR, d))
            
            assert subdrs.version is not None

            versions.add(subdrs.version)

        # Also include versions without files/*_$VERSION
        versions.update(int(x[1:]) for x in os.listdir(self.pub_dir) if x[0] == 'v')

        for version in versions:
            vpath = os.path.join(self.pub_dir, 'v%d' % version)
            if os.path.exists(vpath):
                self.latest = max(version, self.latest)
                self.versions[version] = self._make_version_list(vpath)
            else:
                # Mark missing versions as None
                self.versions[version] = None


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
                # Ignore files matching a regexp
                if re.match(self.drs_tree.drs_fs.IGNORE_FILES_REGEXP, filename):
                    continue

                filepath = os.path.join(dirpath, filename)
                drs = self.drs_tree.drs_fs.filepath_to_drs(filepath)
                vlist.append((filepath, drs))
        return vlist

    #-------------------------------------------------------------------------

    def _deduce_todo(self):
        """
        Filter the drs_tree's incoming list to find new files in this
        PublisherTree.

        """

        drs_cls = self.drs_tree.drs_fs.drs_cls
        filter_components = drs_cls.DRS_ATTRS
        # Remove non-publish-level components
        filter_components = filter_components[:filter_components.index(drs_cls.PUBLISH_LEVEL)+1]

        # Gather DRS components from the template drs instance to filter
        filter = {}
        for comp in filter_components:
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

        fp1 = os.path.realpath(filepath1)
        fp2 = os.path.realpath(filepath2)

        if fp1 != fp2:
            diff_state |= self.DIFF_PATH

        # Check files are the same size
        if _get_size(fp1) != _get_size(fp2):
            diff_state |= self.DIFF_SIZE

        # Check by tracking_id
        if by_tracking_id:
            if fp1[-3:] == fp2[-3:] == '.nc':
                if _get_tracking_id(fp1) != _get_tracking_id(fp2):
                    diff_state |= self.DIFF_TRACKING_ID

        #!TODO: what about md5sum?  This would be slow, particularly as
        #       esgpublish does it anyway.

        return diff_state

    #-------------------------------------------------------------------------
    # Tree checking methods

    def _check_tree(self, fix_hook=None):
        """
        Run a series of checker instances on the object to check for inconsistencies.

        If fix_hook is provided it is called for each failing checker to apply
        any fixes possible.

        """
        ret = True
        self._checker_failures = []
        for Checker in self._checkers:
            checker = Checker()
            log.debug('BEGIN Checking with %s' % checker.get_name())
            if not checker.check(self):
                log.warning('Checker %s failed: %s' % (checker.get_name(), 
                                                       checker.get_message()))
                self._checker_failures.append(checker)
                if fix_hook:
                    fix_hook(checker)
                ret = False
            log.debug('END Checking with %s' % checker.get_name())

        return ret

    def _repair_tree(self):
        """
        Repair inconsistencies that are fixable.

        """
        self._check_tree(self._fix_hook)

    def _fix_hook(self, checker):
        cname = checker.get_name()
        log.debug('Considering repair with %s' % cname)
        if checker.is_fixable():
            log.info('Repairing with %s' % cname)
            try:
                checker.repair(self)
                log.info('Repaired with %s' % cname)
            except:
                log.exception('FAILED repairing with %s' % cname)
        else:
            log.info('Unrepairable %s' % cname)



def _get_tracking_id(filename):
    import cdms2
    ds = cdms2.open(filename)
    tracking_id = ds.tracking_id
    ds.close()
    return tracking_id

def _get_size(filename):
    return os.stat(filename)[stat.ST_SIZE]

