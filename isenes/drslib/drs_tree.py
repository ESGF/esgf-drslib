"""
Classes modelling the DRS directory hierarchy.

"""

from isenes.drslib.cmip5 import make_translator

class DRSTree(object):
    """
    A directory tree in the DRS structure.

    This class needs to persist itself somehow so that it doesn't need
    to scan the whole archive each time it is instantiated.

    Instead it should work out what's new.

    """

    def __init__(self, drs_root):
        self.root_dir = drs_root
        self._trans = make_translator(drs_root)

class RealmTree(object):
    """
    A directory tree at the Realm level.

    """

    STATE_INITIAL = 0
    STATE_VERSIONED_PREPUB = 1
    STATE_VERSIONED_PUB = 2
    STATE_VERSIONED_TRANS = 3

    def __init__(self, drs_root, drs):
        """
        A part of the drs tree containing 1 realm.

        This class works out what state the tree is in

        """

        self.state = None
        self._to_version = []
        self.versions = {}

        self.deduce_state()

    def deduce_state(self):
        #!TODO
        raise NotImplementedError
