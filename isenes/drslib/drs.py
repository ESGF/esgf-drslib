# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''
Created on 25 Jan 2010

@author: Stephen Pascoe

'''

import os
import itertools

class DRS(object):
    """
    Represents a DRS entry.  This class maintains consistency between the
    path and filename portion of the DRS.

    @ivar activity: string
    @ivar product: string
    @ivar institute: string
    @ivar model: string
    @ivar experiment: string
    @ivar frequency: string
    @ivar realm: string
    @ivar variable: string
    @ivar table: string of None
    @ivar ensemble: (r, i, p)
    @ivar version: integer
    @ivar subset: (N1, N2, clim) where N1 and N2 are (y, m, d, h) 
        and clim is boolean
    @ivar extended: A string containing miscellaneous stuff.  Useful for
        representing irregular CMIP3 files

    """

    _drs_attrs = ['activity', 'product', 'institute', 'model', 'experiment', 'frequency', 
                 'realm', 'variable', 'table', 'ensemble', 'version', 'subset', 'extended']

    def __init__(self, **kwargs):
        
        for attr in self._drs_attrs:
            setattr(self, attr, kwargs.get(attr))

    def is_complete(self):
        """Returns boolean to indicate if all components are specified.
        """

        for attr in self._drs_attrs:
            if attr is 'extended':
                continue
            if getattr(self, attr) is None:
                return False

        return True

    def __repr__(self):
        kws = []
        for attr in self._drs_attrs:
            kws.append('%s=%s' % (attr, repr(getattr(self, attr))))
        return '<DRS %s>' % ', '.join(kws)



#--------------------------------------------------------------------------
# A more lightweight way of getting the DRS attributes from a path.
# This is effective for the path part of a DRS path but doesn't verify
# or parse the filename
#

def cmorpath_to_drs(drs_root, path, activity=None):
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
    attrs = ['product', 'institute', 'model', 'experiment',
             'frequency', 'realm', 'variable'] 
    path = [drs_root]
    for attr in attrs:
        val = getattr(drs, attr)
        if val is None:
            break
        path.append(val)

    return os.path.join(*path)
