"""
Classes modelling the DRS directory hierarchy.

"""

import os

from isenes.drslib.cmip5 import make_translator

import logging
log = logging.getLogger(__name__)

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

        self.drs_root = drs_root
        self.drs = drs
        self.state = None
        self._todo = []
        self.versions = {}
        self._vtrans = make_translator(drs_root)
        self._cmortrans = make_translator(drs_root, with_version=False)

        self.realm_dir = os.path.join(self.drs_root,
                                      self.drs.product,
                                      self.drs.institute,
                                      self.drs.model,
                                      self.drs.experiment,
                                      self.drs.frequency,
                                      self.drs.realm)
        if not os.path.exists(self.realm_dir):
            raise RuntimeError('Realm directory %s does not exist' % self.realm_dir)

        self.deduce_state()


    def deduce_state(self):
        """
        Scan the directory structure to work out what state the
        tree is in.

        """

        self._deduce_versions()
        self._deduce_todo()

        #!TODO



    #-------------------------------------------------------------------
    
    def _deduce_versions(self):
        i = 1
        v = self.versions
        while True:
            vpath = os.path.join(self.realm_dir, 'v%d' % i)
            if not os.path.exists(vpath):
                return v

            contents = []
            for dirpath, dirnames, filenames in os.walk(vpath,
                                                        topdown=False):
                for filepath in (os.path.join(dirpath, f) for f in filenames):
                    drs = self._vtrans.filepath_to_drs(filepath)
                    contents.append(drs)
            v['v%d' % i] = contents
            
    def _deduce_todo(self):
        #!WARNING: Only call after _deduce_versions()
        todo = self._todo
        
        for dir in os.listdir(self.realm_dir):
            if dir in self.versions:
                continue

            path = os.path.join(self.realm_dir, dir)
            for dirpath, dirnames, filenames in os.walk(path, topdown=False):
                for filepath in (os.path.join(dirpath, f) for f in filenames):
                    drs = self._cmortrans.filepath_to_drs(filepath)
                    todo.append(drs)
