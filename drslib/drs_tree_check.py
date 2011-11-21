"""
Checker API for checking consistency of PublisherTree instances.

This API adds consistency checking to PublishTrees without bloating the PublisherTree class

"""

import os, sys
from drslib.publisher_tree import VERSIONING_LATEST_DIR

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

    def check(self, pt):
        """

        :param pt: PublisherTree instance to check
        :return: bool for pass or fail
        
        """
        raise NotImplementedError

    def repair(self, pt, data):
        """
        :param pt: PublisherTree instance to check
        """
        raise UnfixableInconsistency()

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
            self._state_fixable('latest directory missing')
        
    def _repair_hook(self, pt):
        pt._do_latest()


class CheckVersionLinks(TreeChecker):
    """
    Check all links in version directories point to real files.

    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self.malformed_paths = []
        self.missing_links = []
        self.wrong_links = []

    def _check_hook(self, pt):
        for version in pt.versions:
            for filepath, drs in pt.versions[version]:
                filepath = os.path.abspath(filepath)

                realdir = pt.real_file_dir(drs.variable, drs.version)
                linkdir = pt.link_file_dir(drs.variable, drs.version)
                filename = os.path.basename(filepath)
                realpath = os.path.abspath(os.path.join(realdir, filename))
                linkpath = os.path.abspath(os.path.join(linkdir, filename))

                # filepath should be deducable from drs
                if os.path.dirname(filepath) != linkdir:
                    self.malformed_paths.append((filepath, linkdir))
                    self._state_unfixable('filepath %s does not match expected path %s' 
                                          % (filepath, linkdir))


                if not os.path.exists(linkpath):
                    self.missing_links.append(linkpath)
                    self._state_unfixable('linkpath %s does not exist' % linkpath)
                    continue

                link = os.readlink(linkpath)
                if not os.path.isabs(link):
                    link = os.path.abspath(os.path.join(linkdir, link))
                linkfile = os.path.basename(link)

                if linkfile != filename:
                    self.wrong_links.append((linkpath, filename))
                    self._state_unfixable('linkpath %s does not point to %s' 
                                          % (linkpath, filename))
                    
                

class CheckVersionFiles(TreeChecker):
    """
    Check all files in file_* are linked to a version directory.

    """

    def __init__(self):
        super(self.__class__, self).__init__()
        self.missing_realpaths = []
        self.missing_linkpaths = []

    def _check_hook(self, pt):
        fv_map = pt.file_version_map()
        versions = pt.versions.keys()

        # for each file check a link exists from that version and all subsequent versions
        #!TODO: this will need changing when file deletion is implemented

        for filename in fv_map:
            variable, fversions = fv_map[filename]

            # deduce subsequent versions
            max_fv = max(fversions)
            later_versions = [v for v in versions if v > max_fv]

            for version in fversions:
                linkpath = os.path.abspath(os.path.join(pt.link_file_dir(variable, version),
                                                        filename))
                realpath = os.path.abspath(os.path.join(pt.real_file_dir(variable, version),
                                                        filename))

                # Check the files exists
                if not os.path.exists(realpath):
                    self.missing_realpaths.append(realpath)
                    self._state_unfixable('realpath %s does not exist' % realpath)
                if not os.path.exists(linkpath):
                    self.missing_linkpaths.append(linkpath)
                    self._state_unfixable('linkpath %s does not exist' % linkpath)

            for version in later_versions:
                # the link should exist but not necessarily the real path
                linkpath = os.path.abspath(os.path.join(pt.link_file_dir(variable, version),
                                                        filename))
                if not os.path.exists(linkpath):
                    self.missing_linkpaths.append(linkpath)
                    self._state_unfixable('linkpath %s does not exist' % linkpath)


default_checkers = [CheckLatest, CheckVersionLinks, CheckVersionFiles]
