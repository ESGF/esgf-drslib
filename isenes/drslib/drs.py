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
