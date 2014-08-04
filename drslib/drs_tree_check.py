"""
Checker API for checking consistency of PublisherTree instances.

This API adds consistency checking to PublishTrees without bloating the PublisherTree class

"""

import os, sys

#!FIXME: DRSFileSystem should hide this now
from drslib.drs import DRSFileSystem
VERSIONING_LATEST_DIR = DRSFileSystem.VERSIONING_LATEST_DIR
VERSIONING_FILES_DIR = DRSFileSystem.VERSIONING_FILES_DIR
IGNORE_FILES_REGEXP = DRSFileSystem.IGNORE_FILES_REGEXP

import os.path as op
import shutil
import re

from drslib.translate import TranslationError, drs_dates_overlap
from drslib.config import check_latest

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
        self._repair_stats = {}

    def get_name(self):
        return getattr(self, 'name', self.__class__.__name__)

    def get_message(self):
        # Override in subclasses for more detailed errors
        if self.state == self.STATE_INITIAL:
            return 'Checks not run yet'
        elif self.state == self.STATE_PASS:
            return 'Checks pass'
        elif self.state == self.STATE_FAIL_FIXABLE:
            return 'Fixable failures'
        elif self.state == self.STATE_FAIL_UNFIXABLE:
            return 'Unfixable failures'
        elif self.state == self.STATE_EXCEPTION:
            return 'Exception raised during checks  Enable logger drslib.drs_tree_check to see full diagnostics'

    def get_stats(self):
        return self._repair_stats

        
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

    def _fs_versions(self, pt):
        return set(int(x[1:]) for x in os.listdir(pt.pub_dir) if x[0] == 'v')

    def _all_versions(self, pt):
        return self._fs_versions(pt).union(pt.versions.keys())
        
    def _latest_version(self, pt):
        versions = self._all_versions(pt)
        if versions:
            return max(self._all_versions(pt))
        else:
            raise ValueError('No latest version')

    #-------------------------------------------------------------------------
    # State changes
    def _state_fixable(self, stat, reason=None):
        if self.state != self.STATE_FAIL_UNFIXABLE:
            self.state = self.STATE_FAIL_FIXABLE
        self._add_stat_count(stat)
        if reason is None:
            reason = ''
        log.warning('Fixable failure: %s: %s' % (stat, reason))

    def _state_unfixable(self, stat, reason=None):
        self.state = self.STATE_FAIL_UNFIXABLE
        self._add_stat_count(stat)
        if reason is None:
            reason = ''
        log.warning('Unfixable failure: %s: %s' % (stat, reason))

    def _state_pass(self):
        self.state = self.STATE_PASS

    def _state_exception(self):
        self.state = self.STATE_EXCEPTION

    def _add_stat_count(self, stat):
        try:
            self._repair_stats[stat] += 1
        except KeyError:
            self._repair_stats[stat] = 1
            


class CheckLatest(TreeChecker):
    def __init__(self):
        super(self.__class__, self).__init__()
        self._fix_to = None

    def _check_hook(self, pt):
        latest_dir = op.join(pt.pub_dir, VERSIONING_LATEST_DIR)

        if not op.exists(latest_dir):
            self._state_fixable('latest directory missing or broken')
            return

        try:
            latest_version = self._latest_version(pt)
        except ValueError:
            return

        # Link could be there but invalid
        link = op.join(pt.pub_dir, os.readlink(latest_dir))
        if not op.exists(link):
            self._state_fixable('Latest directory missing', '%s does not exist' % link)
            self._fix_to = latest_version
            return
        link_v = int(op.basename(op.normpath(link))[1:]) # remove leading "v"
        if link_v != latest_version:
            self._state_fixable('Latest directory wrong', '%s should point to v%d' % (link, latest_version))
            self._fix_to = latest_version
            return

    def _repair_hook(self, pt):
        latest_dir = op.join(pt.pub_dir, VERSIONING_LATEST_DIR)
        if op.islink(latest_dir):
            os.remove(latest_dir)
        if self._fix_to:
            latest_link = op.join(pt.pub_dir, 'v%d' % self._fix_to)
            os.symlink(latest_link, latest_dir)
        else:
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

        # find all filesystem versions and versions from the files directory
        # Only check latest version
        if check_latest == True:
            try:
                versions = [self._latest_version(pt)]
            except ValueError:
                return
        else:
            versions = set(self._all_versions(pt))
        
        for version in versions:
            for stat, message in self._scan_version(pt, version):
                self._state_unfixable(stat, message)
                self._fix_versions.add(version)


    def _scan_version(self, pt, version):
        """
        :return: stat, message
        """
        done = []
        for cmd, src, dest in pt._link_commands(version):
            if cmd == pt.CMD_MKDIR:
                if not op.isdir(dest):
                    yield ('Directory missing', '%s does not exist' % dest)
            elif cmd == pt.CMD_LINK:
                if not op.isabs(src):
                    realsrc = op.abspath(op.join(op.dirname(dest), src))
                else:
                    realsrc = src

                if not op.exists(realsrc):
                    self._state_unfixable('File %s source of link %s does not exist' % (realsrc, dest))
                elif not op.exists(dest):
                    yield ('Missing links', 'Link %s does not exist' % dest)
                else:
                    realdest = os.readlink(dest)
                    if not op.isabs(realdest):
                        realdest = op.abspath(op.join(op.dirname(dest), realdest))

                    if realsrc != realdest:
                        yield ('Links to wrong file', 'Link %s does not point to the correct file %s' % (dest, src))

                    drs = pt.drs_tree.drs_fs.filename_to_drs(op.basename(realsrc))
                    done.append(drs)

        # Now scan filesystem for overlapping files
        version_dir = op.join(pt.pub_dir, 'v%d' % version)
        for dirpath, dirnames, filenames in os.walk(version_dir):
            for filename in filenames:
                try:
                    drs = pt.drs_tree.drs_fs.filename_to_drs(filename)
                except TranslationError:
                    continue
                for done_drs in done:
                    if done_drs.variable == drs.variable and drs_dates_overlap(drs, done_drs):
                        if drs == done_drs:
                            continue
                        log.debug('%s overlaps %s' % (drs, done_drs))
                        yield ('Overlapping files in version', 
                                '%s, %s' % (done_drs, drs))



class CheckFilesLinks(TreeChecker):
    """
    Check to make sure the files directory doesn't contain symbolic links.

    This problem is marked unfixable as to do so would dissrupt old versions.

    """
    def _check_hook(self, pt):
        self._links = []

        latest_version = self._latest_version(pt)
        for filepath, link_dir in pt.iter_real_files():
            if check_latest and version != latest_version:
                continue

            if op.islink(filepath):
                self._links.append((filepath, link_dir))
                self._state_unfixable('Links in files dir', 'Path %s is a symbolic link' % filepath)





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
                # ignore files matching this regexp
                if re.match(IGNORE_FILES_REGEXP, filename):
                    continue

                if not op.islink(op.join(dirpath, filename)):
                    raise UnfixableInconsistency("Version directory %s contains real files" % version_dir)

        # Remove the verison directory
        shutil.rmtree(version_dir)

    # Do all commands to reconstruct the version
    pt._do_commands(pt._link_commands(version))

        
#!NOTE: order is important
default_checkers = [
    #CheckFilesLinks,
    CheckVersionLinks,
    CheckLatest, 
    ]
