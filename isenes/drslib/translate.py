# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Generic implementations of IComponentTranslator

"""

import re, os

class TranslationError(Exception):
    pass

#
# List offsets for the DRS elements in paths and filenames
#

DRS_PATH_ACTIVITY = 0
DRS_PATH_PRODUCT = 1
DRS_PATH_INSTITUTE = 2
DRS_PATH_MODEL = 3
DRS_PATH_EXPERIMENT = 4
DRS_PATH_FREQUENCY = 5
DRS_PATH_REALM = 6
DRS_PATH_VARIABLE = 7
DRS_PATH_ENSEMBLE = 8
DRS_PATH_VERSION = 9

DRS_FILE_VARIABLE = 0
DRS_FILE_TABLE = 1
DRS_FILE_MODEL = 2
DRS_FILE_EXPERIMENT = 3
DRS_FILE_ENSEMBLE = 4
DRS_FILE_SUBSET = 5


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

    """

    _drs_attrs = ['activity', 'product', 'institute', 'model', 'experiment', 'frequency', 
                 'realm', 'variable', 'table', 'ensemble', 'version', 'subset',]

    def __init__(self, **kwargs):
        
        for attr in self._drs_attrs:
            setattr(self, attr, kwargs.get(attr))

    def is_complete(self):
        """Returns boolean to indicate if all components are specified.
        """

        for attr in self._drs_attrs:
            if getattr(self, attr) is None:
                return False

        return True

    def __repr__(self):
        kws = []
        for attr in self._drs_attrs:
            kws.append('%s=%s' % (attr, repr(getattr(self, attr))))
        return '<DRS %s>' % ', '.join(kws)

class TranslatorContext(object):
    """
    Represents a DRS URL or path being translated

    @ivar path_parts: A list of directories following the DRS prefix
    @ivar file_parts: A list of '_'-separated parts of the filename
    @ivar drs: The DRS of interest
    @ivar table_store: The mip tables being used

    """
    def __init__(self, filename=None, path=None, drs=None, table_store=None):
        if path is None:
            self.path_parts = [None] * 10
        else:
            self.path_parts = path.split('/')

        if filename is None:
            self.file_parts = [None] * 6
        else:
            # CMIP3 sometimes uses "." as separator
            self.file_parts = re.split('[_.]', os.path.splitext(filename)[0])
            
        if drs is None:
            self.drs = DRS()
        else:
            self.drs = drs

        self.table_store = table_store

    def set_drs_component(self, drs_component, value):
        """
        Set a DRS component checking that the value doesn't conflict with any current value.

        """
        v = getattr(self.drs, drs_component)
        if v is None:
            setattr(self.drs, drs_component, value)
        else:
            if v != value:
                raise TranslationError('Conflicting value of DRS component %s' % drs_component)

    def path_to_string(self):
        return '/'.join(self.path_parts)
    
    def file_to_string(self):
        # Allow subset to be optional
        if self.file_parts[-1] is None:
            fp = self.file_parts[:-1]
        else:
            fp = self.file_parts
        return '_'.join(fp)
    
    def to_string(self):
        """Returns the full DRS path and filename.
        """
        return '%s/%s.nc' % (self.path_to_string(), self.file_to_string())


class BaseComponentTranslator(object):
    """
    Each component is translated by a separate IComponentTranslator object.

    """

    def filename_to_drs(self, context):
        """
        Translate the relevant component of the filename to a drs component.

        @raises TranslationError: if the filename is invalid
        @returns: context

        """
        raise NotImplementedError

    def path_to_drs(self, context):
        """
        Translate the relevant component of the DRS path to a drs component.

        @raises TranslationError: if the path is invalid
        @returns: context

        """
        raise NotImplementedError


    def drs_to_filepath(self, context):
        """
        Sets context.path_parts and context.file_parts for this component.

        @returns: context

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
            s = self._validate(context.file_parts[self.file_i])
            context.set_drs_component(self.component, s)


    def path_to_drs(self, context):
        if self.path_i is not None:
            s = self._validate(context.path_parts[self.path_i])
            context.set_drs_component(self.component, s)

    def drs_to_filepath(self, context):
        s = self._validate(getattr(context.drs, self.component))
        
        if self.path_i is not None:
            context.path_parts[self.path_i] = s
        if self.file_i is not None:
            context.file_parts[self.file_i] = s

    #----

    def _validate(self, s):
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

    def filename_to_drs(self, context):
        varname = context.file_parts[DRS_FILE_VARIABLE]
        table = context.file_parts[DRS_FILE_TABLE]

        #!TODO: table checking

        context.set_drs_component('variable', varname)
        context.set_drs_component('table', table)


    def path_to_drs(self, context):
        varname = context.file_parts[DRS_PATH_VARIABLE]
        
        #!TODO: table checking

        context.set_drs_component('variable', varname)

    def drs_to_filepath(self, context):
        context.file_parts[DRS_FILE_VARIABLE] = context.drs.variable
        context.file_parts[DRS_FILE_TABLE] = context.drs.table
        context.path_parts[DRS_PATH_VARIABLE] = context.drs.variable


    #----



class EnsembleTranslator(BaseComponentTranslator):
    def filename_to_drs(self, context):
        context.drs.ensemble = self._convert(context.file_parts[DRS_FILE_ENSEMBLE])


    def path_to_drs(self, context):
        context.drs.ensemble = self._convert(context.path_parts[DRS_PATH_ENSEMBLE])


    def drs_to_filepath(self, context):
        (r, i, p) = context.drs.ensemble
        a = ['r%d' % r]
        if i is not None:
            a.append('i%d' % i)
        if p is not None:
            a.append('p%d' % p)
        v = ''.join(a)
        
        context.file_parts[DRS_FILE_ENSEMBLE] = v
        context.path_parts[DRS_PATH_ENSEMBLE] = v


    #----

    def _convert(self, component):
        mo = re.match(r'(?:r(\d+))?(?:i(\d+))?(?:p(\d+))?', component)
        if not mo:
            raise TranslationError('Unrecognised ensemble syntax %s' % component)

        (r, i, p) = mo.groups()
        return (_int_or_none(r), _int_or_none(i), _int_or_none(p))

class VersionTranslator(BaseComponentTranslator):

    def filename_to_drs(self, context):
        pass

    def path_to_drs(self, context):
        context.drs.version = self._convert(context.path_parts[DRS_PATH_VERSION])


    def drs_to_filepath(self, context):
        #!TODO: check component is integer
        context.path_parts[DRS_PATH_VERSION] = 'v%d' % context.drs.version
        
    #----

    def _convert(self, component):
        mo = re.match(r'v(\d+)', component)
        if not mo:
            raise TranslationError('Unrecognised version syntax %s' % component)

        return mo.group(1)

    

class SubsetTranslator(BaseComponentTranslator):
    """
    Currently just temporal subsets

    @cvar allow_missing_subset: A boolean value configuring whether to 
        complain if the subset is missing.

    """

    allow_missing_subset = True

    def filename_to_drs(self, context):
        v = context.file_parts[DRS_FILE_SUBSET]

        if self.allow_missing_subset and not v:
            return
        
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

        context.file_parts[DRS_FILE_SUBSET] = '-'.join(parts)


class Translator(object):
    """

    @property prefix: All paths are interpreted as relative to this prefix.
        Generated paths have this prefix added.
    @property translators: A list of translators called in order to handle translation
    @property table_store: A IMIPTableStore instance containing all MIP tables being used.

    """

    def __init__(self, prefix='', table_store=None):
        self.prefix = prefix
        self.table_store = table_store

    def filename_to_drs(self, filename, context=None):
        if context is None:
            context = TranslatorContext(filename=filename, drs=self.init_drs(),
                                        table_store = self.table_store)
        for t in self.translators:
            t.filename_to_drs(context)

        return context.drs

    def path_to_drs(self, path, context=None):
        if context is None:
            context = TranslatorContext(path=self._split_prefix(path), drs=self.init_drs(),
                                        table_store = self.table_store)
        for t in self.translators:
            t.path_to_drs(context)

        return context.drs

    def filepath_to_drs(self, filepath, context=None):
        filepath = self._split_prefix(filepath)
        path, filename = os.path.split(filepath)
        if context is None:
            context = TranslatorContext(filename=filename, path=path, drs=self.init_drs(),
                                        table_store = self.table_store)
        for t in self.translators:
            t.path_to_drs(context)
            t.filename_to_drs(context)
            
        return context.drs
            
    def drs_to_context(self, drs):
        context = TranslatorContext(drs=self.init_drs(drs), table_store = self.table_store)
        for t in self.translators:
            t.drs_to_filepath(context)

        return context

    def drs_to_filepath(self, drs):
        context = self.drs_to_context(drs)

        return '%s%s' % (self.prefix, context.to_string())

    def drs_to_path(self, drs):
        context = self.drs_to_context(drs)
        
        return '%s%s' % (self.prefix, context.path_to_string())

    def drs_to_file(self, drs):
        context = self.drs_to_context(drs)
        
        return context.file_to_string()

    
    def _split_prefix(self, path):
        n = len(self.prefix)
        if path[:n] == self.prefix:
            return path[n:]
        else:
            #!TODO: warn of missing prefix
            return path

    def init_drs(self):
        """
        Returns an empty DRS instance initialised for this translator.

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
