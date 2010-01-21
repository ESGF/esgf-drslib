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
from datetime import datetime

from isenes.drslib.iface import ITranslator, IComponentTranslator, TranslationError, ITranslatorContext, IDRS

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


class DRS(IDRS):
    _drs_attrs = ['activity', 'product', 'institute', 'model', 'experiment', 'frequency', 
                 'realm', 'variable', 'table', 'ensemble', 'version', 'subset',]

    def __init__(self, **kwargs):
        
        for attr in self._drs_attrs:
            setattr(self, attr, kwargs.get(attr))

    def is_complete(self):
        for attr in self._drs_attrs:
            if getattr(self, attr) is None:
                return False

        return True


class TranslatorContext(ITranslatorContext):
    def __init__(self, filename=None, path=None, drs=None, table_store=None):
        if path is None:
            self.path_parts = [None] * 10
        else:
            self.path_parts = path.split('/')

        if filename is None:
            self.file_parts = [None] * 6
        else:
            self.file_parts = os.path.splitext(filename)[0].split('_')

        if drs is None:
            self.drs = DRS()
        else:
            self.drs = drs

        self.table_store = table_store

    def set_drs_component(self, drs_component, value):
        v = getattr(self.drs, drs_component)
        if v is None:
            setattr(self.drs, drs_component, value)
        else:
            if v != value:
                raise TranslationError('Conflicting value of DRS component %s' % drs_component)

    def to_string(self):
        return '%s/%s.nc' % ('/'.join(self.path_parts),
                             '_'.join(self.file_parts))


class GenericTranslator(IComponentTranslator):
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





class CMORVarTranslator(IComponentTranslator):
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



class EnsembleTranslator(IComponentTranslator):
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

class VersionTranslator(IComponentTranslator):

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

        return re.group(1)

    

class SubsetTranslator(IComponentTranslator):
    """
    Currently just temporal subsets

    """

    def filename_to_drs(self, context):
        v = context.file_parts[DRS_FILE_SUBSET]
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
        (n1, n2, clim) = context.drs.subset

        parts = []
        parts.append(_from_date(n1))
        if n2:
            parts.append(_from_date(n2))
        if clim:
            parts.append('clim')

        context.file_parts[DRS_FILE_SUBSET] = '-'.join(parts)


class Translator(ITranslator):
    def __init__(self, prefix, table_store):
        self.prefix = prefix
        self.table_store = table_store

    #!FIXME: This isn't working!
    def update_drs(self, drs, context=None):
        context = TranslatorContext(drs=self.init_drs(drs), table_store = self.table_store)
        for t in self.translators:
            t.drs_to_filepath(context)

    def filename_to_drs(self, filename):
        context = TranslatorContext(filename=filename, drs=self.init_drs(),
                                    table_store = self.table_store)
        for t in self.translators:
            t.filename_to_drs(context)

        return context.drs

    def path_to_drs(self, path):
        context = TranslatorContext(path=self._split_prefix(path), drs=self.init_drs(),
                                    table_store = self.table_store)
        for t in self.translators:
            t.path_to_drs(context)

        return context.drs

    def drs_to_path(self, drs):
        
        context = TranslatorContext(drs=self.init_drs(drs), table_store = self.table_store)
        for t in self.translators:
            t.drs_to_filepath(context)

        return '%s%s' % (self.prefix, context.to_string())


    def _split_prefix(self, path):
        n = len(self.prefix)
        if path[:n] == prefix:
            return path[n:]
        else:
            #!TODO: warn of missing prefix
            return path

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
