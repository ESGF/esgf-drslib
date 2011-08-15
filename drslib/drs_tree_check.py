"""
Checker API for checking consistency of PublisherTree instances.

This API adds consistency checking to PublishTrees without bloating the PublisherTree class

"""

class UnfixableInconsistency(Exception):
    pass

class TreeChecker(object):
    """
    A PublisherTree is passed to TreeChecker.check() to determine if it is consistent.
    If the test result is false call repair() to fix.

    :cvar name: Name of the checker.  If None get_name() returns the class name

    """

    def check(self, pt):
        """

        :param pt: PublisherTree instance to check
        :return: (test_result, reason)
        
        """

    def repair(self, pt):
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
