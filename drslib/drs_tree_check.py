"""
Checker API for checking consistency of PublisherTree instances.

This API adds consistency checking to PublishTrees without bloating the PublisherTree class

"""

import os, sys
from drslib.publisher_tree import VERSIONING_LATEST_DIR, VERSIONING_FILES_DIR

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
        latest_dir = os.path.join(pt.pub_dir, VERSIONING_LATEST_DIR)

        if not os.path.exists(latest_dir):
            self._state_fixable('latest directory missing or broken')
            return

        # Link could be there but invalid
        link = os.path.join(pt.pub_dir, os.readlink(latest_dir))
        if os.path.exists(link):
            link_v = int(os.path.basename(link)[1:]) # remove leading "v"

            #!FIXME: logic wrong.  pt.latest could be 0
            # Work-arround
            pt._deduce_versions()
            if link_v != pt.latest:
                self._state_fixable('latest directory not pointing to latest version')

        
        
    def _repair_hook(self, pt):
        latest_dir = os.path.join(pt.pub_dir, VERSIONING_LATEST_DIR)
        if os.path.islink(latest_dir):
            os.remove(latest_dir)
        pt._deduce_versions()
        pt._do_latest()


class CheckVersionLinks(TreeChecker):
    """
    Check all links in version directories point to real files.

    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self._fix_commands = []

    def _check_hook(self, pt):
        fdir = os.path.join(pt.pub_dir, VERSIONING_FILES_DIR)
        if not os.path.isdir(fdir):
            self._state_unfixable('Files directory %s does not exist' % fdir)
            return

        # We can't trust pt.versions so deduce versions manually
        versions = set()
        for d in os.listdir(fdir):
            try:
                variable, version = d.split('_')
            except ValueError:
                continue
            versions.add(int(version))

        for version in versions:
            for cmd, src, dest in pt._link_commands(version):
                if cmd == pt.CMD_MKDIR:
                    if not os.path.isdir(dest):
                        self._state_fixable('Directory %s does not exist' % dest)
                        self._fix_commands.append((cmd, src, dest))
                elif cmd == pt.CMD_LINK:
                    if not os.path.isabs(src):
                        realsrc = os.path.abspath(os.path.join(os.path.dirname(dest), src))
                    else:
                        realsrc = src

                    if not os.path.exists(realsrc):
                        self._state_unfixable('File %s source of link %s does not exist' % (realsrc, dest))
                    elif not os.path.exists(dest):
                        self._state_fixable('Link %s does not exist' % dest)
                        self._fix_commands.append((cmd, src, dest))
                    else:
                        realdest = os.readlink(dest)
                        if not os.path.isabs(realdest):
                            realdest = os.path.abspath(os.path.join(os.path.dirname(dest), realdest))
                        
                        if realsrc != realdest:
                            self._state_unfixable('Link %s does not point to the correct file %s' % (dest, src))
                        
                    
    def _repair_hook(self, pt):
        pt._do_commands(self._fix_commands)



#!NOTE: order is important
default_checkers = [CheckVersionLinks,
                    CheckLatest, 
                    ]
