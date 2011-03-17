# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''

The drs module contains a minimal model class for DRS information
and some utility functions for converting filesystem paths to and from
DRS objects.

More sophisticated conversions can be done with the
:mod:`drslib.translate` and :mod:`drslib.cmip5` modules.

'''

import os
import itertools
import re

import logging
log = logging.getLogger(__name__)

DRS_ATTRS = ['activity', 'product', 'institute', 'model', 'experiment', 'frequency', 
             'realm', 'table', 'ensemble', 'version', 'variable', 'subset', 'extended']
PUB_ATTRS = ['activity', 'product', 'institute', 'model', 'experiment', 'frequency', 
             'realm', 'table', 'ensemble', ]

class DRS(dict):
    """
    Represents a DRS entry.  DRS objects are dictionaries where DRS
    components are also exposed as attributes.  Therefore you can get/set
    DRS components using dictionary or attribute notation.

    In combination with the translator machinary, this class maintains
    consistency between the path and filename portion of the DRS.

    :ivar activity: string
    :ivar product: string
    :ivar institute: string
    :ivar model: string
    :ivar experiment: string
    :ivar frequency: string
    :ivar realm: string
    :ivar variable: string
    :ivar table: string of None
    :ivar ensemble: (r, i, p)
    :ivar version: integer
    :ivar subset: (N1, N2, clim) where N1 and N2 are (y, m, d, h) 
        and clim is boolean
    :ivar extended: A string containing miscellaneous stuff.  Useful for
        representing irregular CMIP3 files

    """

    

    def __init__(self, *argv, **kwargs):
        """
        Instantiate a DRS object with a set of DRS component values.

        >>> mydrs = DRS(activity='cmip5', product='output', model='HadGEM1',
        ...             experiment='1pctto4x', variable='tas')
        <DRS activity="cmip5" product="output" model="HadGEM1" ...>

        :param argv: If not () should be a DRS object to instantiate from
        :param kwargs: DRS component values.

        """

        # Initialise all components as None
        for attr in DRS_ATTRS:
            self[attr] = None

        # Check only DRS components are used
        for kw in kwargs:
            if kw not in DRS_ATTRS:
                raise KeyError("Keyword %s is not a DRS component" % repr(kw))

        # Use dict flexible instantiation
        super(DRS, self).__init__(*argv, **kwargs)


    def __getattr__(self, attr):
        if attr in DRS_ATTRS:
            return self[attr]
        else:
            raise AttributeError('%s object has no attribute %s' % 
                                 (repr(type(self).__name__), repr(attr)))

    def __setattr__(self, attr, value):
        if attr in DRS_ATTRS:
            self[attr] = value
        else:
            raise AttributeError('%s is not a DRS component' % repr(attr))

    def is_complete(self):
        """Returns boolean to indicate if all components are specified.
        
        Returns ``True`` if all components except ``extended`` have a value.

        """

        for attr in DRS_ATTRS:
            if attr is 'extended':
                continue
            if self.get(attr, None) is None:
                return False

        return True

    def is_publish_level(self):
        """Returns boolian to indicate if the all publish-level components are
        specified.

        """
        for attr in PUB_ATTRS:
            if self.get(attr, None) is None:
                return False

        return True

    def __repr__(self):
        kws = []
        for attr in DRS_ATTRS:
            kws.append(self._encode_component(attr))

        # Remove trailing '%' from components
        while kws[-1] == '%':
            kws.pop(-1)

        return '<DRS %s>' % '.'.join(kws)

    def _encode_component(self, attr):
        """
        Encode a DRS component as a string.  Components that are None
        are encoded as '%'.

        """
        if self[attr] is None:
            val = '%'
        elif attr is 'ensemble':
            val = self._encode_ensemble()
        elif attr is 'version':
            val = 'v%d' % self.version
        elif attr is 'subset':
            N1, N2, clim = self.subset
            if None in N1:
                val = '%'
                return val
            N1_str = '%04d%02d%02d%02d' % N1
            N2_str = '%04d%02d%02d%02d' % N2
            if clim:
                val = '%s-%s-clim' % (N1_str, N2_str)
            else:
                val = '%s-%s' % (N1_str, N2_str)
        else:
            val = self[attr]

        return val

    def _encode_ensemble(self):
        r, i, p = self.ensemble
        ret = 'r%d' % r
        if i is not None:
            ret += 'i%d' % i
            if p is not None:
                ret += 'p%d' % p

        return ret

    def to_dataset_id(self, with_version=False):
        """
        Return the esgpublish dataset_id for this drs object.
        
        If version is not None and with_version=True the version is included.

        """
        parts = [self._encode_component(x) for x in PUB_ATTRS]
        if self.version and with_version:
            parts.append(self._encode_component('version'))
        return '.'.join(parts)

    @classmethod
    def from_dataset_id(klass, dataset_id, **components):
        """
        Return a DRS object fro a ESG Publisher dataset_id.

        If the dataset_id contains less than 10 components all trailing
        components are set to None.  Any component of value '%' is set to None

        E.g.
        >>> drs = DRS.from_dataset_id('cmip5.output.MOHC.%.rpc45')
        >>> drs.institute, drs.model, drs.experiment, drs.realm
        ('MOHC', None, 'rpc45', None)

        """

        parts = dataset_id.split('.')
        for attr, val in itertools.izip(DRS_ATTRS, parts):
            if val is '%':
                continue
            if attr is 'ensemble':
                r, i, p = re.match(r'r(\d+)i(\d+)p(\d+)', val).groups()
                components[attr] = (int(r), int(i), int(p))
            elif attr is 'version':
                v = re.match(r'v(\d+)', val).group(1)
                components[attr] = int(v)
                # Don't process after version
                break
            else:
                components[attr] = val
                   
        return klass(**components)
            


#--------------------------------------------------------------------------
# A more lightweight way of getting the DRS attributes from a path.
# This is effective for the path part of a DRS path but doesn't verify
# or parse the filename
#

def path_to_drs(drs_root, path, activity=None):
    """
    Create a :class:`DRS` object from a filesystem path.

    This function is more lightweight than using :mod:`drslib.translator`
    but only works for the parts of the DRS explicitly represented in
    a path.

    :param drs_root: The root of the DRS tree.  
        This should point to the *activity* directory

    :param path: The path to convert.  This is either an absolute path
        or is relative to the current working directory.

    """

    nroot = drs_root.rstrip('/') + '/'
    relpath = os.path.normpath(path[len(nroot):])

    p = relpath.split('/')
    attrs = ['product', 'institute', 'model', 'experiment',
             'frequency', 'realm', 'table', 'ensemble'] 
    drs = DRS(activity=activity)
    for val, attr in itertools.izip(p, attrs):
        if attr == 'ensemble':
            mo = re.match(r'r(\d+)i(\d+)p(\d+)', val)
            drs[attr] = tuple(int(x) for x in mo.groups())
        else:
            drs[attr] = val

    log.debug('%s => %s' % (repr(path), drs))

    return drs
    
    
def drs_to_path(drs_root, drs):
    """
    Returns a directory path from a :class:`DRS` object.  Any DRS component
    that is set to None will result in a wildcard '*' element in the path.

    This function does not take into account of MIP tables of filenames.
    
    :param drs_root: The root of the DRS tree.  This should point to
        the *activity* directory
    
    :param drs: The :class:`DRS` object from which to generate the path

    """
    attrs = ['product', 'institute', 'model', 'experiment',
             'frequency', 'realm', 'table', 'ensemble'] 
    path = [drs_root]
    for attr in attrs:
        if drs[attr] is None:
            val = '*'
        else:
            if attr == 'ensemble':
                val = 'r%di%dp%d' % drs.ensemble
            else:
                val = drs[attr]
        if val is None:
            break
        path.append(val)


    #!DEBUG
    assert len(path) == len(attrs)+1

    path = os.path.join(*path)
    log.debug('%s => %s' % (drs, repr(path)))
    return path

