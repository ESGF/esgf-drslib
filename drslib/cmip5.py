# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""

Translate CMIP5 DRS filenames and paths to and from DRS objects with
consistency checking against CMIP5 MIP tables and between the filename
and path portions of filepaths.

"""

import os
import itertools

import drslib.translate as T
from drslib import config
from drslib.mip_table import read_model_table
from drslib.drs import CmipDRS, DRSFileSystem

import logging
log = logging.getLogger(__name__)

class ProductHandler(T.GenericComponentHandler):
    path_i = T.CMIP5_DRS.PATH_PRODUCT
    file_i = None
    component = 'product'
    vocab = None


#!TODO: Get official list.  This is based on Karl's spreadsheet and some educated guesses

# CCSR, CNRM, CSIRO, GFDL, INM, IPSL, LASG, MOHC, MPI-M, MRI, NCAR, NCC, NIMR


model_institute_map = read_model_table(config.model_table)        
cmip3_models = {
    'BCC-CM1': 'CMA',
    'BCM2': 'BCCR',
    'CGCM3-1-T47': 'CCCMA',
    'CGCM3-1-T63': 'CCCMA',
    'CM3': 'CNRM',
    'ECHO-G': 'MIUB-KMA',
    'MK3': 'CSIRO',
    'MK3-5': 'CSIRO',
    'CM2': 'GFDL',
    'CM2-1': 'GFDL',
    'CM3': 'INM',
    'CM4': 'IPSL',
    'FGOALS-G1-0': 'LASG',
    'ECHAM5': 'MPIM',
    'CGCM2-3-2': 'MRI',
    'GISS-AOM': 'NASA',
    'GISS-EH': 'NASA',
    'GISS-ER': 'NASA',
    'CCSM3': 'NCAR',
    'PCM': 'NCAR',
    'MIROC3-2-HI': 'NIES',
    'MIROC3-2-MED': 'NIES',
    'HADCM3': 'UKMO',
    'HADGEM1': 'UKMO',
    'ECHAM4': 'INGV',
    
    # Models from CMOR test suite
    'GICCM1': 'TEST',

    # Models in test listings contributed from MPI
    'ECHAM6-MPIOM-HR': 'MPI-M',
    'ECHAM6-MPIOM-LR': 'MPI-M',
}
for k in cmip3_models:
    if k in model_institute_map:
        raise Exception("Duplicate model %s" % k)
    model_institute_map[k] = cmip3_models[k]
# Add overrides from the config file
for institute, models in config.institutes.items():
    for model in models:
        model_institute_map[model] = institute
 

class InstituteHandler(T.GenericComponentHandler):
    path_i = T.CMIP5_DRS.PATH_INSTITUTE
    file_i = None
    component = 'institute'
    vocab = model_institute_map.values()

    def filename_to_drs(self, context):
        context.drs.institute = self._deduce_institute(context)

    def drs_to_filepath(self, context):
        if context.drs.institute is None:
            context.drs.institute = self._deduce_institute(context)

        super(InstituteHandler, self).drs_to_filepath(context)        

    #----

    def _deduce_institute(self, context):
        model = context.drs.model
        if context.drs.institute:
            return context.drs.institute
        try:
            return model_institute_map[model]
        except KeyError:
            log.warn('Institute translation requires model to be known')
            return None


    # Allow all institutes
    def _validate(self, s):
        return s


#!TODO: Not official identifiers
class ModelHandler(T.GenericComponentHandler):
    path_i = T.CMIP5_DRS.PATH_MODEL
    file_i = T.CMIP5_DRS.FILE_MODEL
    component = 'model'
    vocab = model_institute_map.keys()

    def _validate(self, s):
        # Demote validation errors to a warning.
        try:
            return super(ModelHandler, self)._validate(s)
        except T.TranslationError, e:
            log.warning('Model validation error: %s', e)
        return s

model_t = ModelHandler()

class ExperimentHandler(T.GenericComponentHandler):
    path_i = T.CMIP5_DRS.PATH_EXPERIMENT
    file_i = T.CMIP5_DRS.FILE_EXPERIMENT
    component = 'experiment'
    #!NOTE: Set CMIP3 and decadal experiments in metaconfig.
    vocab = set()

    def __init__(self, table_store):
        super(ExperimentHandler, self).__init__(table_store)

        # Get valid experiment ids from MIP tables
        for table in self.table_store.tables.values():
            self.vocab.update(table.experiments)

        # Get valid experiment ids from metaconfig
        self.vocab.update(config.experiments)

class FrequencyHandler(T.GenericComponentHandler):
    path_i = T.CMIP5_DRS.PATH_FREQUENCY
    file_i = None
    component = 'frequency'

    def __init__(self, table_store):
        super(FrequencyHandler, self).__init__(table_store)

        self.vocab = set()
        for table in self.table_store.tables.values():
            try:
                self.vocab.add(table.frequency)
            except AttributeError:
                pass

    def filename_to_drs(self, context):
        context.drs.frequency = self._deduce_freq(context)

    def drs_to_filepath(self, context):
        # If context.drs.frequency is None it could be deduced from the MIP table
        if context.drs.frequency is None:
            context.drs.frequncy = self._deduce_freq(context)

        return super(FrequencyHandler, self).drs_to_filepath(context)
            
    #----

    def _deduce_freq(self, context):
        # Read frequency from MIP table
        table = context.drs.table
        variable = context.drs.variable
        if (table is None) or (variable is None):
            raise T.TranslationError('Frequency translation requires table and variable to be known')

        return context.table_store.get_global_attr(table, 'frequency')
        

#!TODO: Get this information from CMIP tables
class RealmHandler(T.GenericComponentHandler):
    path_i = T.CMIP5_DRS.PATH_REALM
    file_i = None
    component = 'realm'

    def __init__(self, table_store):
        super(RealmHandler, self).__init__(table_store)

        # Extract valid realms from the MIP tables
        self.vocab = set()
        for table in table_store.tables.values():
            for var in table.variables:
                try:
                    realms = table.get_variable_attr(var, 'modeling_realm')[0]
                except AttributeError:
                    pass
                else:
                    realms = realms.split()
                    self.vocab.update(realms)

    def _validate(self, s):
        # Multi-valued realms.  self._validate automatically selects
        # the first realm to put in the DRS syntax.
        #!TODO: smarter algorithm for deciding main realm
        if ' ' in s:
            s = s.split(' ')[0]

        return super(RealmHandler, self)._validate(s)

    def filename_to_drs(self, context):
        try:
            context.drs.realm = self._deduce_realm(context)
        except T.TranslationError:
            log.warning("Realm translation not possible.  You must provide the realm manually")

    def drs_to_filepath(self, context):
        # If context.drs.realm is None it could be deduced from the MIP table
        if context.drs.realm is None:
            context.drs.realm = self._deduce_realm(context)

        return super(RealmHandler, self).drs_to_filepath(context)


    #----

    def _deduce_realm(self, context):
        # Read realm from MIP table
        table = context.drs.table
        variable = context.drs.variable
        if (table is None) or (variable is None):
            raise T.TranslationError('Realm translation requires table and variable to be known')

        try:
            val = context.table_store.get_variable_attr(table, variable, 'modeling_realm')
        except ValueError:
            raise T.TranslationError

        return self._validate(val)



class ExtendedHandler(T.BaseComponentHandler):
    """
    The extended DRS component is only used when converting DRS->filename.
    It is needed for CMIP3 conversions.
    
    """
    component = None

    def drs_to_filepath(self, context):
        context.file_parts[T.CMIP5_DRS.FILE_EXTENDED] = context.drs.extended
        
    def path_to_drs(self, context):
        pass
    
    def filename_to_drs(self, context):
        pass
    



class CMIP5Translator(T.Translator):
    def init_drs(self, drs=None):
        if drs is None:
            drs = T.CmipDRS()

        if drs.activity is None:
            drs.activity = config.drs_defaults.get('activity', 'cmip5')

        return drs

_table_store = None
def get_table_store():
    """
    Return a :class:`drslib.mip_table.MIPTableStore` object
    containing the CMIP5 MIP tables available.

    """
    global _table_store
    from drslib.mip_table import MIPTableStore

    if _table_store is None:
        _table_store = MIPTableStore('%s/%s*' % (config.table_path, 
                                                 config.table_prefix))

    return _table_store

def make_translator(prefix, with_version=True, table_store=None):
    """
    Return a :class:`drslib.translate.Translator` object for
    translating filepaths to and from ``DRS`` instances.

    :param prefix: The path to the root of the DRS tree.  This should
        point to the DRS ``activity`` directory.

    :param with_version: If ``True`` the translator will include a
        version directory in filesystem paths, otherwise it reflects
        the output structure of CMOR.

    :param table_store:: Override default table store.

    """

    if table_store is None:
        table_store = get_table_store()

    t = CMIP5Translator(prefix, table_store)
    t.handlers = [
        T.GridspecHandler(table_store),
        ProductHandler(table_store),
        ModelHandler(table_store),

        # Must follow model_t
        InstituteHandler(table_store),
        ExperimentHandler(table_store),
        ]

    if with_version:
        t.handlers += [
            T.VersionedEnsembleHandler(table_store),
            T.VersionedVarHandler(table_store),
            ]
    else:
        t.handlers += [
            T.EnsembleHandler(table_store),
            T.CMORVarHandler(table_store),
            ]
        
    t.handlers += [
        # Must be processed after variable
        RealmHandler(table_store),
        FrequencyHandler(table_store),
        ]

    if with_version:
        t.handlers.append(T.VersionHandler(table_store))

    t.handlers += [
        T.SubsetHandler(table_store),
        ExtendedHandler(table_store),
        ]


    return t



class CMIP5FileSystem(DRSFileSystem):
    drs_cls = CmipDRS

    def __init__(self, drs_root, table_store=None):
        super(CMIP5FileSystem, self).__init__(drs_root)

        self._vtrans = make_translator(self.drs_root, table_store=table_store)

    def filename_to_drs(self, filename):
        return self._vtrans.filename_to_drs(filename)

    def filepath_to_drs(self, filepath):
        return self._vtrans.filepath_to_drs(filepath)

    def drs_to_storage(self, drs):
        return '%s/%s_%s' % (self.VERSIONING_FILES_DIR,
            self.drs_cls._encode_component('variable', drs.variable),
            #!NOTE: _encode_component would add "v" to the beginning
            drs.version)

    def storage_to_drs(self, subpath):
        filesdir, subpath2 = subpath.split('/')
        variable_str, version_str = subpath2.split('_')

        variable = self.drs_cls._decode_component('variable', variable_str)
        version = self.drs_cls._decode_component('version', version_str)

        return self.drs_cls(variable=variable, version=version)

    def drs_to_linkpath(self, drs, version=None):
        if version is None:
            version = drs.version

        pubpath = self.drs_to_publication_path(drs)
        return os.path.abspath(os.path.join(pubpath, 'v%d' % version,
                                            drs.variable))

