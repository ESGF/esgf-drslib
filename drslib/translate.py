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

import re, os

import logging
log = logging.getLogger(__name__)

from drslib.drs import DRS
from drslib.config import CMIP5_DRS, CMIP5_CMOR_DRS

class TranslationError(Exception):
    pass


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
            
        if drs is None:
            self.drs = DRS()
        else:
            self.drs = drs

        self.table_store = table_store

    def set_drs_component(self, drs_component, value):
        """
        Set a DRS component checking that the value doesn't conflict
        with any current value.

        """
        v = self.drs[drs_component]
        if v is None:
            setattr(self.drs, drs_component, value)
        else:
            if v != value:
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


class BaseComponentTranslator(object):
    """
    Each component is translated by a separate IComponentTranslator object.

    """

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

class GenericComponentTranslator(BaseComponentTranslator):
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





class CMORVarTranslator(BaseComponentTranslator):
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

class VersionedVarTranslator(CMORVarTranslator):
    file_var_i = CMIP5_DRS.FILE_VARIABLE
    file_table_i = CMIP5_DRS.FILE_TABLE
    path_var_i = CMIP5_DRS.PATH_VARIABLE
    path_table_i = CMIP5_DRS.PATH_TABLE

    def path_to_drs(self, context):
        super(VersionedVarTranslator, self).path_to_drs(context)

        tablename = context.path_parts[self.path_table_i]

        context.set_drs_component('table', tablename)

    def drs_to_filepath(self, context):
        super(VersionedVarTranslator, self).drs_to_filepath(context)

        context.path_parts[self.path_table_i] = context.drs.table

class EnsembleTranslator(BaseComponentTranslator):
    file_i = CMIP5_CMOR_DRS.FILE_ENSEMBLE
    path_i = CMIP5_CMOR_DRS.PATH_ENSEMBLE

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
        mo = re.match(r'(?:r(\d+))?(?:i(\d+))?(?:p(\d+))?', component)
        if not mo:
            raise TranslationError('Unrecognised ensemble syntax %s' % component)

        (r, i, p) = mo.groups()
        return (_int_or_none(r), _int_or_none(i), _int_or_none(p))

class VersionedEnsembleTranslator(EnsembleTranslator):
    file_i = CMIP5_DRS.FILE_ENSEMBLE
    path_i = CMIP5_DRS.PATH_ENSEMBLE


class VersionTranslator(BaseComponentTranslator):

    def filename_to_drs(self, context):
        pass

    def path_to_drs(self, context):
        context.drs.version = self._convert(context.path_parts[CMIP5_DRS.PATH_VERSION])


    def drs_to_filepath(self, context):
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

    

class SubsetTranslator(BaseComponentTranslator):
    """
    Currently just temporal subsets

    :cvar allow_missing_subset: A boolean value configuring whether to 
        complain if the subset is missing.

    """

    allow_missing_subset = True

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


class Translator(object):
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
        for t in self.translators:
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
        for t in self.translators:
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
        for t in self.translators:
            t.path_to_drs(context)
            t.filename_to_drs(context)
            
        return context.drs
            
    def drs_to_context(self, drs):
        context = self.ContextClass(drs=self.init_drs(drs), table_store = self.table_store)
        for t in self.translators:
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


def _to_date(date_str):
    mo = re.match(r'(\d{4})(\d{2})?(\d{2})?(\d{2})?', date_str)
    if not mo:
        raise ValueError()

    (y, m, d, h) = mo.groups()
    return (int(y), _int_or_none(m), _int_or_none(d), _int_or_none(h))

def _from_date(date):
    (y, m, d, h) = date

    ret = ['%d' % y]
    if m is not None:
        ret.append('%02d' % m)
    if d is not None:
        ret.append('%02d' % d)
    if h is not None:
        ret.append('%02d' % h)
    return ''.join(ret)
    
def _int_or_none(x):
    if x is None:
        return None
    else:
        return int(x)
