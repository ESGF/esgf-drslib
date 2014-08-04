# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
A framework for translating DRS objects to and from filenames and paths.

This module is very object-heavy and over engineered.  However, it does the job.

"""

#!TODO: CORDEX.  Completely reimplement translation in a more flexible manner
#       Maybe use the Python logic programming library used by IRIS.  We should
#       keep this implementation for cmip5 only and try to reimplement CMIP5 logic
#       in the new interface when possible.

import re, os

import logging
log = logging.getLogger(__name__)

from drslib.drs import CmipDRS, _rip_to_ensemble, _ensemble_to_rip, _int_or_none
from drslib.config import CMIP5_DRS, CMIP5_CMOR_DRS
from drslib.exceptions import TranslationError
from drslib.translate_iface import BaseTranslator


#-----------------------------------------------------------------------------
# Legacy implementation of BaseTranslator
#
# This implementation of BaseTranslator uses individual
# ComponentHandler classes to handle each DRS component and a
# TranslatorContext class to hold the state of the translation.
#
# NOTE: ComponentHandler classes were originally called
#       ComponentTranslator classes.  This was confusing thus
#       the rename.

class TranslatorContext(object):
    """
    Represents a DRS URL or path being translated.

    :ivar path_parts: A list of directories following the DRS prefix
    :ivar file_parts: A list of '_'-separated parts of the filename
    :ivar drs: The DRS of interest
    :ivar table_store: The mip tables being used.

    """
    def __init__(self, filename=None, path=None, drs=None, table_store=None):
        if path is None:
            self.path_parts = [None] * 12
        else:
            self.path_parts = path.split('/')

        if filename is None:
            self.file_parts = [None] * 7
        else:
            self.file_parts = os.path.splitext(filename)[0].split('_')
            
        # Work-arround because CMOR encodes 'clim' as flag as _clim
        if self.file_parts[-1] == 'clim':
            self.file_parts[-2:] = [self.file_parts[-2] + '-clim']

        if drs is None:
            self.drs = CmipDRS()
        else:
            self.drs = drs

        self.table_store = table_store

        # Set of components that have been set to override
        self._override = set()

    def set_drs_component(self, drs_component, value, override=False):
        """
        Set a DRS component checking that the value doesn't conflict
        with any current value.

        If override is True the component is marked as overriden and future
        attempts to set it will be ignored

        """
        if override:
            self._override.add(drs_component)

        v = self.drs[drs_component]
        if v is None:
            setattr(self.drs, drs_component, value)
        else:
            if v != value and drs_component not in self._override:
                raise TranslationError('Conflicting value of DRS component %s' % drs_component)


    def path_to_string(self):
        self._trim_parts()

        parts = self.path_parts
        
        return os.path.join(*parts)
    
    def file_to_string(self):
        # To allow optional portions any None's are removed
        fp = [x for x in self.file_parts if x is not None]

        # Check there is at last 1 item in the list
        assert len(fp) > 0

        return '_'.join(fp)+'.nc'
    
    def to_string(self):
        """Returns the full DRS path and filename.
        """
        self._trim_parts()

        return os.path.join(self.path_to_string(), self.file_to_string())

    def _trim_parts(self):
        """Remove extranious Nones from path_parts and file_parts.
        """

        while self.path_parts[-1] is None:
            self.path_parts.pop()

        while self.file_parts[-1] is None:
            self.file_parts.pop()


class Translator(BaseTranslator):
    """
    An abstract class for translating between filepaths and
    :class:`drslib.drs.DRS` objects.

    Concrete subclasses are returned by factory functions such as
    :mod:`drslib.cmip5.make_translator`.

    :property prefix: The prefix for all DRS paths including the
        activity.  All paths are interpreted as relative to this
        prefix.  Generated paths have this prefix added.

    :property table_store: A :class:`drslib.mip_table.MIPTableStore`
        object containing all MIP tables being used.
    
    """

    ContextClass = TranslatorContext

    def __init__(self, prefix='', table_store=None):
        self.prefix = prefix
        self.table_store = table_store

    def filename_to_drs(self, filename, context=None):
        """
        Translate a filename into a :class:`drslib.drs.DRS` object.

        Only those DRS components known from the filename will be set.

        """

        if context is None:
            context = self.ContextClass(filename=filename, drs=self.init_drs(),
                                        table_store = self.table_store)
        for t in self.handlers:
            if t.component in context._override:
                continue

            t.filename_to_drs(context)

        return context.drs

    def path_to_drs(self, path, context=None):
        """
        Translate a directory path into a :class:`drslib.drs.DRS`
        object.
        
        Only those DRS components known from the path will be set.

        """
        if context is None:
            context = self.ContextClass(path=self._split_prefix(path), drs=self.init_drs(),
                                        table_store = self.table_store)
        for t in self.handlers:
            if t.component in context._override:
                continue
            t.path_to_drs(context)

        return context.drs

    def filepath_to_drs(self, filepath, context=None):
        """
        Translate a full filepath to a :class:`drslib.drs.DRS` object.

        """
        filepath = self._split_prefix(filepath)
        path, filename = os.path.split(filepath)
        if context is None:
            context = self.ContextClass(filename=filename, path=path, drs=self.init_drs(),
                                        table_store = self.table_store)
        for t in self.handlers:
            if t.component in context._override:
                continue
            
            t.path_to_drs(context)
            t.filename_to_drs(context)
            
        return context.drs
            
    def drs_to_context(self, drs):
        context = self.ContextClass(drs=self.init_drs(drs), table_store = self.table_store)
        for t in self.handlers:
            if t.component in context._override:
                continue
            t.drs_to_filepath(context)

        return context

    def drs_to_filepath(self, drs):
        """
        Translate a :class:`drslib.drs.DRS` object into a full filepath.

        """
        context = self.drs_to_context(drs)

        return os.path.join(self.prefix, context.to_string())

    def drs_to_path(self, drs):
        """
        Translate a :class:`drslib.drs.DRS` object into a directory path.

        """
        context = self.drs_to_context(drs)
        
        return os.path.join(self.prefix, context.path_to_string())

    def drs_to_file(self, drs):
        """
        Translate a :class:`drslib.drs.DRS` object into a filename.

        """
        context = self.drs_to_context(drs)
        
        return context.file_to_string()

    
    def _split_prefix(self, path):
        n = len(self.prefix)
        if path[:n] == self.prefix:
            return path[n:].lstrip('/')
        else:
            log.warn('Path %s does not have prefix %s' % (path, self.prefix))
            return path

    def init_drs(self):
        """
        Returns an empty DRS instance initialised for this translator.

        This class must be overloaded in subclasses.

        """
        raise NotImplementedError


#-----------------------------------------------------------------------------
# Component handlers

class BaseComponentHandler(object):
    """
    Each component is translated by a separate IComponentHandler object.

    """
    component = None

    def __init__(self, table_store=None):
        self.table_store = table_store

    def filename_to_drs(self, context):
        """
        Translate the relevant component of the filename to a drs component.

        :raises TranslationError: if the filename is invalid
        :returns: context

        """
        raise NotImplementedError

    def path_to_drs(self, context):
        """
        Translate the relevant component of the DRS path to a drs component.

        :raises TranslationError: if the path is invalid
        :returns: context

        """
        raise NotImplementedError


    def drs_to_filepath(self, context):
        """
        Sets context.path_parts and context.file_parts for this component.

        :returns: context

        """
        raise NotImplementedError

class GenericComponentHandler(BaseComponentHandler):
    """
    The simplest type of translator just validating strings

    """

    # Class attributes set in subclasses
    path_i = NotImplemented
    file_i = NotImplemented
    component = NotImplemented
    vocab = NotImplemented

    def filename_to_drs(self, context):
        if self.file_i is not None:
            try:
                s = self._validate(context.file_parts[self.file_i])
            except IndexError:
                raise TranslationError("Filename contains too few components")
            context.set_drs_component(self.component, s)


    def path_to_drs(self, context):
        if self.path_i is not None:
            s = self._validate(context.path_parts[self.path_i])
            context.set_drs_component(self.component, s)

    def drs_to_filepath(self, context):
        s = self._validate(context.drs[self.component])
        
        if self.path_i is not None:
            context.path_parts[self.path_i] = s
        if self.file_i is not None:
            context.file_parts[self.file_i] = s

    #----

    def _validate(self, s):
        if self.vocab is None:
            return s

        if s not in self.vocab:
            raise TranslationError('Component value %s not in vocabulary of component %s' % (s, self.component))

        return s


class GridspecHandler(BaseComponentHandler):
    """
    Gridspec files don't fit into drslib's architecture very well
    so this is a work-around.  variable is set to "gridspec".
    """
    component = None

    def filename_to_drs(self, context):
        if context.file_parts[0] == 'gridspec':
            assert context.file_parts[2] == 'fx'
            realm = context.file_parts[1]
            model = context.file_parts[3]
            experiment = context.file_parts[4]
            ensemble = (0, 0, 0)

            context.set_drs_component('variable', 'gridspec', override=True)
            context.set_drs_component('realm', realm, override=True)
            context.set_drs_component('model', model, override=True)
            context.set_drs_component('experiment', experiment, override=True)
            context.set_drs_component('ensemble', ensemble, override=True)
            context.set_drs_component('frequency', 'fx', override=True)
            context.set_drs_component('table', 'fx', override=True)
            context.set_drs_component('ensemble', (0, 0, 0), override=True)
            #!FIXME: Hack
            context._override.add('subset')

    def path_to_drs(self, context):
        pass
    
    def drs_to_filepath(self, context):
        if context.drs.variable != 'gridspec':
            return

        context.file_parts[0] = 'gridspec'
        context.file_parts[1] = context.drs.realm
        context.file_parts[2] = context.drs.frequency
        context.file_parts[3] = context.drs.model
        context.file_parts[4] = context.drs.experiment
        context.file_parts[5] = _ensemble_to_rip(context.drs.ensemble)

        context.path_parts[2] = context.drs.model
        context.path_parts[3] = context.drs.experiment
        context.path_parts[4] = context.drs.frequency
        context.path_parts[5] = context.drs.realm
        context.path_parts[6] = context.drs.table
        context.path_parts[7] = _ensemble_to_rip(context.drs.ensemble)
        context.path_parts[9] = context.drs.variable
        #!FIXME: Hack
        context._override.update(['variable', 'realm', 'frequency', 'model', 
                                  'experiment', 'table', 'ensemble'])




class CMORVarHandler(BaseComponentHandler):
    """
    CMIP Variable translator

    For CMIP5, each variable is uniquely identified by a combination
    of two strings: 1) a name associated generically with the variable
    (typically, as recorded in the netCDF file ? e.g., tas, pr, ua),
    and 2) the name of the CMOR variable table (e.g., Amon, da, aero)
    in which the variable appears. Together these two strings ensure
    that the variable is uniquely 4 defined. There are some
    applications in which the second string might be unnecessary
    (e.g., for CMIP5, this will be omitted from the directory
    structure). Note that for CMIP5 a hyphen ('-') is forbidden to be
    included anywhere in the first string.

    """

    file_var_i = CMIP5_CMOR_DRS.FILE_VARIABLE
    file_table_i = CMIP5_CMOR_DRS.FILE_TABLE
    path_var_i = CMIP5_CMOR_DRS.PATH_VARIABLE
    component = 'variable'

    def filename_to_drs(self, context):
        varname = context.file_parts[self.file_var_i]
        table = context.file_parts[self.file_table_i]

        #!TODO: table checking

        context.set_drs_component('variable', varname)
        context.set_drs_component('table', table)


    def path_to_drs(self, context):
        varname = context.file_parts[self.file_var_i]
        
        #!TODO: table checking

        context.set_drs_component('variable', varname)

    def drs_to_filepath(self, context):
        context.file_parts[self.file_var_i] = context.drs.variable
        context.file_parts[self.file_table_i] = context.drs.table
        context.path_parts[self.path_var_i] = context.drs.variable


    #----

class VersionedVarHandler(CMORVarHandler):
    file_var_i = CMIP5_DRS.FILE_VARIABLE
    file_table_i = CMIP5_DRS.FILE_TABLE
    path_var_i = CMIP5_DRS.PATH_VARIABLE
    path_table_i = CMIP5_DRS.PATH_TABLE
    component = 'variable'

    def path_to_drs(self, context):
        super(VersionedVarHandler, self).path_to_drs(context)

        tablename = context.path_parts[self.path_table_i]

        context.set_drs_component('table', tablename)

    def drs_to_filepath(self, context):
        super(VersionedVarHandler, self).drs_to_filepath(context)

        context.path_parts[self.path_table_i] = context.drs.table

class EnsembleHandler(BaseComponentHandler):
    file_i = CMIP5_CMOR_DRS.FILE_ENSEMBLE
    path_i = CMIP5_CMOR_DRS.PATH_ENSEMBLE
    component = 'ensemble'

    def filename_to_drs(self, context):
        context.drs.ensemble = self._convert(context.file_parts[self.file_i])


    def path_to_drs(self, context):
        context.drs.ensemble = self._convert(context.path_parts[self.path_i])


    def drs_to_filepath(self, context):
        (r, i, p) = context.drs.ensemble
        a = ['r%d' % r]
        if i is not None:
            a.append('i%d' % i)
        if p is not None:
            a.append('p%d' % p)
        v = ''.join(a)
        
        context.file_parts[self.file_i] = v
        context.path_parts[self.path_i] = v


    #----

    def _convert(self, component):
        return _rip_to_ensemble(component)

class VersionedEnsembleHandler(EnsembleHandler):
    file_i = CMIP5_DRS.FILE_ENSEMBLE
    path_i = CMIP5_DRS.PATH_ENSEMBLE
    component = 'ensemble'

class VersionHandler(BaseComponentHandler):
    component = 'version'

    def filename_to_drs(self, context):
        pass

    def path_to_drs(self, context):
        context.drs.version = self._convert(context.path_parts[CMIP5_DRS.PATH_VERSION])


    def drs_to_filepath(self, context):
        if context.drs.version is not None:
            context.path_parts[CMIP5_DRS.PATH_VERSION] = 'v%d' % context.drs.version
        
    #----

    def _convert(self, component):
        mo = re.match(r'v(\d+)', component)
        if not mo:
            raise TranslationError('Unrecognised version syntax %s' % component)

        try:
            v = int(mo.group(1))
        except TypeError:
            raise TranslationError('Unrecognised version syntax %s' % component)

        return v

    

class SubsetHandler(BaseComponentHandler):
    """
    Currently just temporal subsets

    :cvar allow_missing_subset: A boolean value configuring whether to 
        complain if the subset is missing.

    """

    allow_missing_subset = True
    component = 'subset'

    def filename_to_drs(self, context):
        try:
            v = context.file_parts[CMIP5_DRS.FILE_SUBSET]
        except IndexError:
            if self.allow_missing_subset:
                return
            else:
                raise TranslationError('Missing temporal subset')
        
        mo = re.match(r'(\d+)(?:-(\d+))?(-clim)?', v)
        if not mo:
            raise TranslationError('Unrecognised temporal subset %s' % v)

        n1, n2, clim = mo.groups()
        if clim: 
            clim=True

        context.drs.subset = (_to_date(n1), _to_date(n2), clim)


    def path_to_drs(self, component):
        pass

    def drs_to_filepath(self, context):

        if self.allow_missing_subset and context.drs.subset is None:
            return
                
        (n1, n2, clim) = context.drs.subset
        
        parts = []
        parts.append(_from_date(n1))
        if n2:
            parts.append(_from_date(n2))
        if clim:
            parts.append('clim')

        context.file_parts[CMIP5_DRS.FILE_SUBSET] = '-'.join(parts)





#-----------------------------------------------------------------------------
# Date conversion and comparison functions

#!TODO: CORDEX.  Move into DRS class.  Maybe implement within DRS._encode_component()
def _to_date(date_str):
    if date_str is None:
        return None

    mo = re.match(r'(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?', date_str)
    if not mo:
        raise ValueError()

    (y, m, d, h, mn, sec) = mo.groups()
    return (int(y), _int_or_none(m), _int_or_none(d), _int_or_none(h), _int_or_none(mn), _int_or_none(sec))

#!TODO: CORDEX. As above.
def _from_date(date):
    (y, m, d, h, mn, sec) = date

    ret = ['%04d' % y]
    if m is not None:
        ret.append('%02d' % m)
    if d is not None:
        ret.append('%02d' % d)
    if h is not None:
        ret.append('%02d' % h)
    if mn is not None:
        ret.append('%02d' % mn)
    if sec is not None:
        ret.append('%02d' % sec)
    return ''.join(ret)

def drs_dates_overlap(drs1, drs2):
    if drs1.subset is None or drs2.subset is None:
        return False
    range1, range2 = sorted((drs1.subset[:2], drs2.subset[:2]))

    d11, d12 = range1
    d21, d22 = range2

    # Special case
    if d11 == d12 == d21 == d22:
        return True

    return d21 < d12
        
    
