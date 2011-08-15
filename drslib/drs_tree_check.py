"""
Checker API for checking consistency of PublisherTree instances.

This API adds consistency checking to PublishTrees without bloating the PublisherTree class

"""

import os, sys
from drslib.publisher_tree import VERSIONING_LATEST_DIR

class UnfixableInconsistency(Exception):
    pass


class TreeChecker(object):
    """
    A PublisherTree is passed to TreeChecker.check() to determine if it is consistent.
    If the test result is false call repair(data) to fix.

    :cvar name: Name of the checker.  If None get_name() returns the class name.

    """

    def check(self, pt):
        """

        :param pt: PublisherTree instance to check
        :return: (result, reason, data)
        
        """

    def repair(self, pt, data):
        """
        :param pt: PublisherTree instance to check
        """
        raise UnfixableInconsistency()

    def get_name(self):
        name = self.get('name')

        if name is None:
            return self.__class__.__name__
        else:
            return name


class CheckLatest(TreeChecker):
    def __init__(self):
        pass

    def check(self, pt):
        latest_dir = os.path.join(pt.pub_dir, VERSIONING_LATEST_DIR)
        if not os.path.exists(latest_dir):
            return (False, 'latest directory missing', None)
        
        return (True, '', None)

default_checkers = [CheckLatest()]
