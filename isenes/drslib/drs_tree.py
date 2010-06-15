"""
Classes modelling the DRS directory hierarchy.

"""

import os
from glob import glob

from isenes.drslib.cmip5 import make_translator
from isenes.drslib.drs import DRS, cmorpath_to_drs, drs_to_cmorpath

import logging
log = logging.getLogger(__name__)

class DRSTree(object):
    """
    Manage a Data Reference Syntax directory structure.

    """

    def __init__(self, drs_root):
        self.drs_root = drs_root
        self.realm_trees = []
        
        
    def discover(self, product, institute, model, experiment=None,
                 frequency=None, realm=None):
        """
        Scan the directory structure for RealmTrees.

        This implementation is a compromise between the need to
        auto-discover RealmTrees and the fact that scanning the entire
        DRSTree may be infeasible.  You must specify the are of the
        DRS to scan up to the model level.

        """

        drs = DRS(product=product, institute=institute, model=model,
                  experiment=experiment, frequency=frequency, realm=realm)

        if not frequency:
            drs.frequency = '*'
        if not realm:
            drs.realm = '*'
        if not experiment:
            drs.experiment = '*'

        rt_glob = drs_to_cmorpath(self.drs_root, drs)
        realm_trees = glob(rt_glob)
        for rt_path in realm_trees:
            drs = cmorpath_to_drs(self.drs_root, rt_path)
            self.realm_trees.append(RealmTree(self.drs_root, drs))

class RealmTree(object):
    """
    A directory tree at the Realm level.

    """

    STATE_INITIAL = 0
    STATE_VERSIONED = 1
    STATE_VERSIONED_TRANS = 2

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


    @classmethod
    def from_path(Class, path):
        """
        Construct a RealmTree from a realm-level filesystem path.

        """
        p = os.path.normpath(os.path.abspath(path))
        p, realm = os.path.split(p)
        p, frequency = os.path.split(p)
        p, experiment = os.path.split(p)
        p, model = os.path.split(p)
        p, institute = os.path.split(p)
        p, product = os.path.split(p)
        drs_root = p

        drs = DRS(realm=realm, frequency=frequency, experiment=experiment,
                  model=model, institute=institute, product=product)

        return Class(drs_root, drs)

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


    def do_version(self):
        """
        Move incoming files into the next version

        """
        #!TODO
        raise NotImplementedError

    #-------------------------------------------------------------------
    
    def _deduce_versions(self):
        i = 1
        v = self.versions
        while True:
            vpath = os.path.join(self.realm_dir, 'v%d' % i)
            if not os.path.exists(vpath):
                self._next_version = i
                return v

            contents = []
            for dirpath, dirnames, filenames in os.walk(vpath,
                                                        topdown=False):
                for filepath in (os.path.join(dirpath, f) for f in filenames):
                    drs = self._vtrans.filepath_to_drs(filepath)
                    contents.append(drs)
            v['v%d' % i] = contents
            
            i += 1
            
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
