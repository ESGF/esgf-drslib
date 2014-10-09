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

from drslib.cmip5 import CMIP5FileSystem
from drslib.translate import TranslationError
from drslib import config, mapfile
from drslib.p_cmip5 import ProductException
from drslib.publisher_tree import PublisherTree

import logging
log = logging.getLogger(__name__)

# We also want to log to p_cmip5 so that product detection can be filtered sensibly
p_cmip5_log = logging.getLogger('drslib.p_cmip5')


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

    def __init__(self, drs_fs):
        """
        :param drs_root: The path to the DRS *activity* directory.
        :param table_store: Override the default table store.  This can be used
            to select the TAMIP tables.

        """
        self.drs_fs = drs_fs

        self.pub_trees = {}
        self.incoming = DRSList()
        self.incomplete = DRSList()

        #!TODO: generalise output specification callback
        self._p_cmip5 = None

        self._move_cmd = config.move_cmd


        if not os.path.isdir(self.drs_fs.drs_root):
            raise Exception('DRS root "%s" is not a directory' % self.drs_fs.drs_root)

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

        drs_t = self.drs_fs.drs_cls(**components)

        # NOTE: None components are converted to wildcards
        pt_glob = self.drs_fs.drs_to_publication_path(drs_t)
        pub_trees = glob(pt_glob)

        for pt_path in pub_trees:
            # Detect whether pt_path is inside incoming.  If so ignore.
            if incoming_dir and (os.path.commonprefix((pt_path+'/', incoming_dir+'/')) == incoming_dir+'/'):
                log.warning("PublisherTree path %s is inside incoming, ignoring" % pt_path)
                continue

            drs = self.drs_fs.publication_path_to_drs(pt_path, activity=drs_t.activity)
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
        files independently of :meth:`DRSTree.discover`.

        :incoming_dir: A directory to recursively scan for files.

        """

        def _iter_incoming():
            for dirpath, dirnames, filenames in os.walk(incoming_dir):
                for filename in filenames:
                    yield (filename, dirpath)

        self.discover_incoming_fromfiles(_iter_incoming(), **components)


    def iter_drspaths_fromfiles(self, files_iter, **components):
        for filename, dirpath in files_iter:
            log.debug('Processing %s' % filename)
            try:
                drs = self.drs_fs.filename_to_drs(filename)
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

                yield (filename, dirpath, drs)


    def discover_incoming_fromdrspaths(self, drspaths_iter):
        """
        Process a stream of files into the incoming list from an
        iterable of (filename, dirpath, drs)

        """

        for (filename, dirpath, drs) in drspaths_iter:
            if drs.is_publish_level():
                log.debug('Discovered %s as %s' % (filename, drs))
                self.incoming.append((os.path.join(dirpath, filename), drs))
            else:
                log.debug('Rejected %s as incomplete %s' % (filename, drs))
                self.incomplete.append((os.path.join(dirpath, filename), drs))

        # Instantiate a PublisherTree for each unique publication-level dataset
        for path, drs in self.incoming:
            drs_id = drs.to_dataset_id()
            if drs_id not in self.pub_trees:
                self.pub_trees[drs_id] = PublisherTree(drs, self)

        for pt in self.pub_trees.values():
            pt.deduce_state()

    def discover_incoming_fromfiles(self, files_iter, **components):
        """
        Process a stream of files into the incoming list from an
        iterable.

        This method is useful as a low-level hook for integrating
        with processing pipelines.

        :files_iter: An iterable of (filename, path) for
            each file to process into incoming.

        """
        return self.discover_incoming_fromdrspaths(
            self.iter_drspaths_fromfiles(files_iter, **components))

    def discover_incoming_fromjson(self, json_obj, **components):
        """
        Process a stream of files into the incoming list from a
        json object.

        This method is useful as a low-level hook for integrating
        with processing pipelines.

        :json_obj: A list of dictionaries {'path': path, 'drs': drs} where drs is
           a dictionary of drs terms.

        """
        return self.discover_incoming_fromdrspaths(
            self.iter_drspaths_fromjson(json_obj, **components))


    def iter_drspaths_fromjson(self, json_obj, **components):
        """

        :json_obj: A list of dictionaries {'path': path, 'drs': drs}

        """
        for d in json_obj:
            path = d['path']
            filename = os.path.basename(path)
            dirpath = os.path.dirname(path)
            drs_cls = self.drs_fs.drs_cls

            # construct a drs from the filename
            drs = self.drs_fs.filename_to_drs(os.path.basename(path))

            # Construct the DRS object from the json dictionary
            drs2 = drs_cls.from_json(d['drs'], **components)            
            
            drs.update(drs2)

            yield (filename, dirpath, drs)
            

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
            startyear = None
        else:
            startyear = drs.subset[0][0]

        try:
            status = pci.find_product(drs.variable, drs.table, drs.experiment, drs.model,
                                      path, startyear=startyear)
            # Make sure status is consistent with no exceptions being raised
            assert status
        except ProductException as e:
            p_cmip5_log.warn('FAILED product detection for %s, %s' % (drs, e))
        else:
            p_cmip5_log.debug('%s, %s, %s, %s:: %s %s' % (drs.variable, drs.table, drs.experiment, 
                                                                 path, 
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

        

