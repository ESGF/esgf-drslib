"""
Checker API for checking consistency of PublisherTree instances.

This API adds consistency checking to PublishTrees without bloating the PublisherTree class

"""

import os, sys
from drslib.publisher_tree import VERSIONING_LATEST_DIR, VERSIONING_FILES_DIR
import os.path as op
import shutil

from drslib.translate import TranslationError, drs_dates_overlap


import logging
log = logging.getLogger(__name__)

class UnfixableInconsistency(Exception):
    pass


class TreeChecker(object):
    """
    A PublisherTree is passed to TreeChecker.check() to determine if it is consistent.
    If the test result is false call repair() to fix.

    :cvar name: Name of the checker.  If None get_name() returns the class name.
    :ivar state: status of checker.  Whether it has been run, pass or fail.

    """

    STATE_INITIAL = 1
    STATE_PASS = 2
    STATE_FAIL_FIXABLE = 3
    STATE_FAIL_UNFIXABLE = 4
    STATE_EXCEPTION = 5

    def __init__(self):
        self.state = self.STATE_INITIAL

    def get_name(self):
        return getattr(self, 'name', self.__class__.__name__)

    def get_message(self):
        # Override in subclasses for more detailed errors
        if self.state == self.STATE_INITIAL:
            return 'Checks not run yet'
        elif self.state == self.STATE_PASS:
            return 'Checks pass'
        elif self.state == self.STATE_FAIL_FIXABLE:
            return 'Checks fail and can be fixed'
        elif self.state == self.STATE_FAIL_UNFIXABLE:
            return 'Checks fail and are unfixable'
        elif self.state == self.STATE_EXCEPTION:
            return 'Exception raised during checks'
        
    def has_passed(self):
        return self.state == self.STATE_PASS

    def is_fixable(self):
        return self.state == self.STATE_FAIL_FIXABLE

    def check(self, pt):
        try:
            self._state_pass()
            self._check_hook(pt)
        except:
            self._state_exception()
            raise

        return self.has_passed()

    def repair(self, pt):
        try:
            self._repair_hook(pt)
        except:
            self._state_exception()
            raise

        # Recheck after fixing
        self.check(pt)

        return self.has_passed()

    def _check_hook(self, pt):
        # Implement in subclasses
        raise NotImplementedError

    def _repair_hook(self, pt):
        # Implement in subclasses
        raise NotImplementedError


    #-------------------------------------------------------------------------
    # State changes
    def _state_fixable(self, reason=None):
        if self.state != self.STATE_FAIL_UNFIXABLE:
            self.state = self.STATE_FAIL_FIXABLE
        if reason:
            log.warning('Fixable failure: %s' % reason)

    def _state_unfixable(self, reason=None):
        self.state = self.STATE_FAIL_UNFIXABLE
        if reason:
            log.warning('Unfixable failure: %s' % reason)

    def _state_pass(self):
        self.state = self.STATE_PASS

    def _state_exception(self):
        self.state = self.STATE_EXCEPTION


class CheckLatest(TreeChecker):
    def __init__(self):
        super(self.__class__, self).__init__()

    def _check_hook(self, pt):
        latest_dir = op.join(pt.pub_dir, VERSIONING_LATEST_DIR)

        if not op.exists(latest_dir):
            self._state_fixable('latest directory missing or broken')
            return

        # Link could be there but invalid
        link = op.join(pt.pub_dir, os.readlink(latest_dir))
        if op.exists(link):
            link_v = int(op.basename(link)[1:]) # remove leading "v"

            #!FIXME: logic wrong.  pt.latest could be 0
            # Work-arround
            pt._deduce_versions()
            if link_v != pt.latest:
                self._state_fixable('latest directory not pointing to latest version')

        
        
    def _repair_hook(self, pt):
        latest_dir = op.join(pt.pub_dir, VERSIONING_LATEST_DIR)
        if op.islink(latest_dir):
            os.remove(latest_dir)
        pt._deduce_versions()
        pt._do_latest()


class CheckVersionLinks(TreeChecker):
    """
    Check all links in version directories point to real files.

    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self._fix_versions = set()

    def _check_hook(self, pt):
        fdir = op.join(pt.pub_dir, VERSIONING_FILES_DIR)
        if not op.isdir(fdir):
            self._state_unfixable('Files directory %s does not exist' % fdir)
            return

        for version in pt.versions.keys():
            ok, message = self._scan_version(pt, version)
            if not ok:
                self._state_fixable(message)
                self._fix_versions.add(version)


    def _scan_version(self, pt, version):
        done = []
        for cmd, src, dest in pt._link_commands(version):
            if cmd == pt.CMD_MKDIR:
                if not op.isdir(dest):
                    return (False, 'Directory %s does not exist' % dest)
            elif cmd == pt.CMD_LINK:
                if not op.isabs(src):
                    realsrc = op.abspath(op.join(op.dirname(dest), src))
                else:
                    realsrc = src

                if not op.exists(realsrc):
                    self._state_unfixable('File %s source of link %s does not exist' % (realsrc, dest))
                elif not op.exists(dest):
                    return (False, 'Link %s does not exist' % dest)
                else:
                    realdest = os.readlink(dest)
                    if not op.isabs(realdest):
                        realdest = op.abspath(op.join(op.dirname(dest), realdest))

                    if realsrc != realdest:
                        return (False, 'Link %s does not point to the correct file %s' % (dest, src))

                    drs = pt._vtrans.filename_to_drs(op.basename(realsrc))
                    done.append(drs)

        # Now scan filesystem for overlapping files
        version_dir = op.join(pt.pub_dir, 'v%d' % version)
        for dirpath, dirnames, filenames in os.walk(version_dir):
            for filename in filenames:
                try:
                    drs = pt._vtrans.filename_to_drs(filename)
                except TranslationError:
                    continue
                for done_drs in done:
                    if drs_dates_overlap(drs, done_drs):
                        #!FIXME: I think this could still be fooled
                        if drs == done_drs:
                            continue
                        log.debug('%s overlaps %s' % (drs, done_drs))
                        return (False, 'Overlaping files in v%s' % version)

        return (True, None)
                    
    def _repair_hook(self, pt):
        for version in self._fix_versions:
            repair_version(pt, version)


class CheckFilesLinks(TreeChecker):
    """
    Check to make sure the files directory doesn't contain symbolic links.

    """
    def _check_hook(self, pt):
        self._links = []

        for filepath, variable, version in pt.iter_real_files():
            if op.islink(filepath):
                self._links.append((filepath, variable, version))
                self._state_fixable('Path %s is a symbolic link' % filepath)

    def _repair_hook(self, pt):
        for filepath, variable, version in self._links:
            log.info('Removing bad link %s' % filepath)
            # Last sanity check
            assert op.islink(filepath)
            os.remove(filepath)

            # Remove directory if empty
            fdir = op.dirname(filepath)
            if os.listdir(fdir) == []:
                log.info('Removing empty directory %s' % fdir)
                os.rmdir(fdir)

        # Re-deduce versions
        pt._deduce_versions()


class CheckOrphanedVersions(TreeChecker):
    """
    In some circumstances a version directory shouldn't be there because there
    are no corresponding files/<var>_<version> directories.

    In this case we flag the dataset as unfixable as manual intervention will
    be required.  In most cases the best course of action will be to rename
    a previous version as this new version in order to ensure latest versions
    remain current.
    
    """
    def _check_hook(self, pt):
        pt._deduce_versions()

        for vdir in os.listdir(pt.pub_dir):
            if vdir[0] != 'v':
                continue
            try:
                version = int(vdir[1:])
            except TypeError:
                continue

            if version not in pt.versions.keys():
                self._state_unfixable('Version %s is orphaned.  You should manually rename the previous version' % version)


def repair_version(pt, version):
    """
    An 'all in one' repair function that removes the version directory
    and reconstructs from scratch.

    This function is guaranteed not to delete anything if real files
    are detected in the version directory.

    """

    log.info('Reconstructing version %d' % version)

    version_dir = op.join(pt.pub_dir, 'v%d' % version)
    if op.isdir(version_dir):
        # First verify no real files exist in the version directory
        for dirpath, dirnames, filenames in os.walk(version_dir):
            for filename in filenames:
                if not op.islink(op.join(dirpath, filename)):
                    raise UnfixableInconsistency("Version directory %s contains real files" % version_dir)

        # Remove the verison directory
        shutil.rmtree(version_dir)

    # Do all commands to reconstruct the version
    pt._do_commands(pt._link_commands(version))

        
#!NOTE: order is important
default_checkers = [
    CheckFilesLinks,
    CheckVersionLinks,
    CheckOrphanedVersions,
    CheckLatest, 
    ]
