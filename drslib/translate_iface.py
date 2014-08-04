# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from abc import ABCMeta


#-----------------------------------------------------------------------------
# BaseTranslator interface

class BaseTranslator(object):
    """
    An abstract class for translating between filepaths and
    :class:`drslib.drs.DRS` objects.

    Concrete subclasses are returned by factory functions such as
    :mod:`drslib.cmip5.make_translator`.

    :property prefix: The prefix for all DRS paths including the
        activity.  All paths are interpreted as relative to this
        prefix.  Generated paths have this prefix added.

    """

    __metaclass__ = ABCMeta

    def __init__(self, prefix=''):
        raise NotImplementedError

    def filename_to_drs(self, filename):
        """
        Translate a filename into a :class:`drslib.drs.DRS` object.

        Only those DRS components known from the filename will be set.

        """
        raise NotImplementedError

    def path_to_drs(self, path):
        """
        Translate a directory path into a :class:`drslib.drs.DRS`
        object.
        
        Only those DRS components known from the path will be set.

        """
        raise NotImplementedError

    def filepath_to_drs(self, filepath):
        """
        Translate a full filepath to a :class:`drslib.drs.DRS` object.

        """
        raise NotImplementedError
            
    def drs_to_filepath(self, drs):
        """
        Translate a :class:`drslib.drs.DRS` object into a full filepath.

        """
        raise NotImplementedError

    def drs_to_path(self, drs):
        """
        Translate a :class:`drslib.drs.DRS` object into a directory path.

        """
        raise NotImplementedError

    def drs_to_file(self, drs):
        """
        Translate a :class:`drslib.drs.DRS` object into a filename.

        """
        raise NotImplementedError
    
