# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Manage DRS directory structure versioning.

This module provides an API for manipulating a DRS directory structure
to facilitate keeping multiple versions of datasets on disk
simultaniously.  The class :class:`DRSTree` provides a top-level
interface to the DRS directory structure and a container for :class:`PublisherTree` objects.

:class:`PublisherTree` objects expose the versions present in a
publication-level dataset and what files are unversioned.  Calling
:meth:`PublisherTree.do_version` will manipulate the directory structure
to move unversioned files into a new version.

Detailed diagnostics can be logged by setting handlers for the logger
``drslib.drs_tree``.


"""

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

# We also want to log to p_cmip5 so that product detection can be filtered sensibly
p_cmip5_log = logging.getLogger('drslib.p_cmip5')

#---------------------------------------------------------------------------
# DRY definitions

VERSIONING_FILES_DIR = 'files'
VERSIONING_LATEST_DIR = 'latest'

#---------------------------------------------------------------------------

class DRSTree(object):
    """
    Manage a Data Reference Syntax directory structure.

    A DRSTree represents the root of a DRS hierarchy.  Also associated
    with DRSTree objects is a incoming directory pattern that is
    searched for files matching the DRS structure.  Any file within
    the incoming tree will be considered for new versions of PublisherTrees.

    :ivar incoming: :class:`DRSList` of (filepath, DRS) of all files to be added to the
                    DRSTree on next upgrade.
    :ivar incomplete: :class:`DRSList` of (filepath, DRS) of all files rejected because
                      of incomplete DRS attributes.

    """

    def __init__(self, drs_root, table_store=None):
        """
        :param drs_root: The path to the DRS *activity* directory.
        :param table_store: Override the default table store.  This can be used
            to select the TAMIP tables.

        """
        self.drs_root = drs_root
        self.pub_trees = {}
        self._vtrans = make_translator(drs_root, table_store=table_store)
        self.incoming = DRSList()
        self.incomplete = DRSList()
        self._p_cmip5 = None

        self._move_cmd = config.move_cmd

        if not os.path.isdir(drs_root):
            raise Exception('DRS root "%s" is not a directory' % self.drs_root)

    def discover(self, incoming_dir=None, **components):
        """
        Scan the directory structure for PublisherTrees.

        To prevent an exaustive scan of the directory structure some
        components of the DRS must be specified as keyword arguments
        or configured via *metaconfig*.  These components are
        *product*, *institute* and *model* 

        The components *experiment*, *frequency* and *realm* are
        optional.  All components can be set to wildcard values.  This
        allows an exaustive scan to be forced if desired.

        :incoming_dir: A filesystem wildcard which should resolve to 
            directories to recursively scan for files.  If None no incoming
            files are detected

        """
        
        drs_t = DRS(**components)

        # NOTE: None components are converted to wildcards
        pt_glob = drs_to_path(self.drs_root, drs_t)
        pub_trees = glob(pt_glob)
        for pt_path in pub_trees:
            # Detect whether pt_path is inside incoming.  If so ignore.
            if incoming_dir and (os.path.commonprefix((pt_path+'/', incoming_dir+'/')) == incoming_dir+'/'):
                log.warning("PublisherTree path %s is inside incoming, ignoring" % pt_path)
                continue

            drs = path_to_drs(self.drs_root, pt_path)
            #!FIXME: Set inside path_to_drs?
            drs.activity = drs_t.activity
            drs_id = drs.to_dataset_id()
            if drs_id in self.pub_trees:
                raise Exception("Duplicate PublisherTree %s" % drs_id)

            log.info('Discovered PublisherTree at %s' % pt_path)
            self.pub_trees[drs_id] = PublisherTree(drs, self)

        # Scan for incoming DRS files
        if incoming_dir:
            self.discover_incoming(incoming_dir, **components)


        
    def discover_incoming(self, incoming_dir, **components):
        """
        Scan the filesystem for incoming DRS files.

        This method can be repeatedly called to discover incoming
        files independently of :meth:`DRSTree.discover` repeatedly .

        :incoming_dir: A directory to recursively scan for files.

        """

        def _iter_incoming():
            for dirpath, dirnames, filenames in os.walk(incoming_dir):
                for filename in filenames:
                    yield (filename, dirpath)

        self.discover_incoming_fromfiles(_iter_incoming(), **components)


    def discover_incoming_fromfiles(self, files_iter, **components):
        """
        Process a stream of files into the incoming list from an
        iterable.

        This method is useful as a low-level hook for integrating
        with processing pipelines.

        :files_iter: An iterable of (filename, path) for
            each file to process into incoming.

        """
        for filename, dirpath in files_iter:
            log.debug('Processing %s' % filename)
            try:
                drs = self._vtrans.filename_to_drs(filename)
            except TranslationError:
                # File doesn't match
                log.warn('File %s is not a DRS file' % filename)
                continue

            log.debug('File %s => %s' % (repr(filename), drs))
            for k, v in components.items():
                if v is None:
                    continue
                # If component is present in drs act as a filter
                drs_v = drs.get(k, None)
                if drs_v is not None:
                    if drs_v != v:
                        log.warn('FILTERED OUT: %s.  %s != %s' %
                                  (drs, repr(drs_v), repr(v)))
                        break
                else:
                    # Otherwise set as default
                    log.debug('Set %s=%s' % (k, repr(v)))
                    setattr(drs, k, v)
            else:
                # Only if break not called

                # Detect product if enabled
                if self._p_cmip5:
                    self._detect_product(dirpath, drs)

                if drs.is_publish_level():
                    log.debug('Discovered %s as %s' % (filename, drs))
                    self.incoming.append((os.path.join(dirpath, filename), drs))
                else:
                    log.debug('Rejected %s as incomplete %s' % (filename, drs))
                    self.incomplete.append((os.path.join(dirpath, filename), drs))
                # Instantiate a PublisherTree for each unique publication-level dataset

        for path, drs in self.incoming:
            drs_id = drs.to_dataset_id()
            if drs_id in self.pub_trees:
                self.pub_trees[drs_id].deduce_state()
            else:
                self.pub_trees[drs_id] = PublisherTree(drs, self)


            
    def remove_incoming(self, path):
        # Remove path from incoming
        #!TODO: This isn't efficient.  Refactoring of incoming or _todo required.
        for npath, drs in self.incoming:
            if path == npath:
                self.incoming.remove((npath, drs))
                break
        else:
            # not found
            raise Exception("File %s not found in incoming" % path)

    def set_p_cmip5(self, p_cmip5):
        """
        Set the :class:`p_cmip5.product.cmip5_product` instance used to deduce
        the DRS product component.

        """
        self._p_cmip5 = p_cmip5

    def _detect_product(self, path, drs):
        """
        Use the p_cmip5 module to deduce the product of this DRS object.
        p_cmip5 must be configured by calling :meth:`DRSTree.set_p_cmip5`.

        """
        p_cmip5_log.info('Deducing product for %s' % drs)

        pci = self._p_cmip5
        if drs.subset is None or drs.subset[0] == None:
            startyear = endyear = None
        else:
            startyear = drs.subset[0][0]
            endyear = drs.subset[1][0]

        try:
            status = pci.find_product(drs.variable, drs.table, drs.experiment, drs.model,
                                      path, startyear=startyear, endyear=endyear)
            # Make sure status is consistent with no exceptions being raised
            assert status
        except ProductScope as e:
            p_cmip5_log.warn('FAILED product detection for %s, %s' % (drs, e))
        else:
            if startyear and endyear:
                dur_str = '%d-%d' % (startyear, endyear)
            else:
                dur_str = ''
            p_cmip5_log.debug('%s, %s, %s, %s, %s:: %s %s' % (drs.variable, drs.table, drs.experiment, 
                                                                 path, dur_str,
                                                                 pci.product, pci.reason ))
            
            drs.product = pci.product
            p_cmip5_log.info('Product deduced as %s, %s' % (drs.product, pci.reason))

    def set_move_cmd(self, cmd):
        self._move_cmd = cmd

    def incomplete_dataset_ids(self):
        """
        Return a set of dataset ids for each publication-level dataset that detect_incoming()
        has found as incomplete.
        
        """
        if self.incomplete is None:
            return set()
        else:
            return set(drs.to_dataset_id() for fp, drs in self.incomplete)

class DRSList(list):
    """
    A list of tuples (filepath, DRS) objects offering a simple query interface.

    """

    def select(self, **kw):
        """Select all DRS objects with given component values.
        
        For each key in ``kw`` if the value is a list select all
        DRS objects with values in that list, otherwise select
        all objects with that value.

        """
        items = self
        for k, v in kw.items():
            if type(v) == list:
                items = [x for x in items if x[1].get(k, None) in v]
            else:
                items = [x for x in items if x[1].get(k, None) == v]

        return DRSList(items)

        

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
                    pfilepath = os.path.realpath(os.path.join(os.path.dirname(prevlink),
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

