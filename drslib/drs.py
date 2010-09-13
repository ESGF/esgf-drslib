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

    _drs_attrs = ['activity', 'product', 'institute', 'model', 'experiment', 'frequency', 
                 'realm', 'variable', 'table', 'ensemble', 'version', 'subset', 'extended']

    def __init__(self, **kwargs):
        """
        Instantiate a DRS object with a set of DRS component values.

        >>> mydrs = DRS(activity='cmip5', product='output', model='HadGEM1',
        ...             experiment='1pctto4x', variable='tas')
        <DRS activity="cmip5" product="output" model="HadGEM1" ...>

        :param kwargs: DRS component values.

        """

        for attr in self._drs_attrs:
            setattr(self, attr, kwargs.get(attr))

    def __getattr__(self, attr):
        if attr in self._drs_attrs:
            return self[attr]
        else:
            raise AttributeError('%s object has no attribute %s' % 
                                 (repr(type(self).__name__), repr(attr)))

    def __setattr__(self, attr, value):
        if attr in self._drs_attrs:
            self[attr] = value
        else:
            raise AttributeError('%s is not a DRS component' % repr(attr))

    def is_complete(self):
        """Returns boolean to indicate if all components are specified.
        
        Returns ``True`` if all components except ``extended`` have a value.

        """

        for attr in self._drs_attrs:
            if attr is 'extended':
                continue
            if self.get(attr, None) is None:
                return False

        return True

    def __repr__(self):
        kws = []
        for attr in self._drs_attrs:
            kws.append('%s=%s' % (attr, repr(self[attr])))
        return '<DRS %s>' % ', '.join(kws)

    def to_dataset_id(self):
        """
        Return the esgpublish dataset_id for this drs object.
        
        """
        return '.'.join((self.activity, self.product, self.institute, self.model,
                         self.experiment, self.frequency, self.realm,
                         self.table, 'r%di%dp%d' % self.ensemble))
                    



#--------------------------------------------------------------------------
# A more lightweight way of getting the DRS attributes from a path.
# This is effective for the path part of a DRS path but doesn't verify
# or parse the filename
#

def cmorpath_to_drs(drs_root, path, activity=None):
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
             'frequency', 'realm', 'variable'] 
    drs = DRS(activity=activity)
    for val, attr in itertools.izip(p, attrs):
        setattr(drs, attr, val)

    return drs
        
def drs_to_cmorpath(drs_root, drs):
    """
    Returns a directory path from a :class:`DRS` object.

    This function does not take into account of MIP tables of filenames.
    
    :param drs_root: The root of the DRS tree.  This should point to
        the *activity* directory
    
    :param drs: The :class:`DRS` object from which to generate the path

    """
    attrs = ['product', 'institute', 'model', 'experiment',
             'frequency', 'realm', 'variable'] 
    path = [drs_root]
    for attr in attrs:
        val = drs[attr]
        if val is None:
            break
        path.append(val)

    return os.path.join(*path)

