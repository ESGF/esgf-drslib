# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
A translator specific to CMIP5

"""

import isenes.drslib.translate as T
import isenes.drslib.config as config

class ActivityTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_ACTIVITY
    file_i = None
    component = 'activity'
    vocab = ['cmip5', 'cmip3']
    


activity_t = ActivityTranslator()

class ProductTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_PRODUCT
    file_i = None
    component = 'product'
    vocab = ['output', 'requested']
product_t = ProductTranslator()


#!TODO: Get official list.  This is based on Karl's spreadsheet and some educated guesses
model_institution_map = {
        'NorESM': 'NorClim', 
        'MRI-CGCM3': 'MRI', 
        'MRI-ESM1': 'MRI', 
        'MRI-AM20km': 'MRI',
        'MRI-AM60km': 'MRI', 
        'MIROC4-2-M': 'NIES', 
        'MIROC4-2-H': 'NIES', 
        'MIROC3-2-M': 'NIES',
        'MIROC-ESM': 'NIES', 
        'IPSL-CM6': 'IPSL', 
        'IPSL-CM5': 'IPSL', 
        'INMCM4': 'INM',
        'HiGEM1-2': 'NERC-UKMO', 
        'HadGEM2-ES': 'UKMO', 
        'HadGEM2-AO': 'NIMR', 
        'HadCM3Q': 'UKMO',
        'HadCM3': 'UKMO', 
        'GFDL-HIRAM': 'GFDL',
        'GFDL-ESM2G': 'GFDL', 
        'GFDL-ESM2M': 'GFDL',
        'GFDL-CM3': 'GFDL', 
        'GFDL-CM2-1': 'GFDL', 
        'FGOALS-S2': 'LASG', 
        'FGOALS-G2': 'LASG',
        'FGOALS-gl': 'LASG', 
        'ECHAM5-MPIOM': 'MPI-M', 
        'CSIRO-Mk3-5A': 'CSIRO', 
        'CCSM4-H': 'NCAR',
        'CCSM4-M': 'NCAR', 
        'CNRM-CM5': 'CNRM', 
        'CanESM2': 'CCCMA', 
        'ACCESS': 'CAWCR', 
        'BCC-CSM': 'BCCR',
}

#!TODO: Get full list.  This is based on CMIP3
class InstituteTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_INSTITUTE
    file_i = None
    component = 'institute'
    vocab = model_institution_map.values()

    def filename_to_drs(self, context):
        model = context.drs.model
        if model is None:
            raise T.TranslationError('Institute translation requires model to be known')

        context.drs.institute = model_institution_map[model]

institute_t = InstituteTranslator()


#!TODO: Not official identifiers
class ModelTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_MODEL
    file_i = T.DRS_FILE_MODEL
    component = 'model'
    vocab = model_institution_map.keys()
model_t = ModelTranslator()

class ExperimentTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_EXPERIMENT
    file_i = T.DRS_FILE_EXPERIMENT
    component = 'experiment'
    vocab = [
        'decadalXXXX', #!TODO: replace XXXX with decades
        'noVolcano',
        'volcano2010',
        'piControl',
        'historical',
        'midHolocene',
        'lgm',
        'past1000',
        'rcp45',
        'rcp85',
        'rcp26',
        'rcp60',
        'esmControl',
        'esmHistorical',
        'esmRcp85',
        'esmFixClim1',
        'esmFixClim2',
        'esmFdbk1',
        'esmFdbk2',
        'lpctCo2',
        'abrupt4xco2',

        'historicalNat',
        'historicalAnt',
        'historicalGhg', 
        'historicalSd', 
        'historicalSi', 
        'historicalSa', 
        'historicalTo', 
        'historicalSo', 
        'historicalOz', 
        'historicalLu', 
        'historicalSl', 
        'historicalVl', 
        'historicalSs', 
        'historicalDs', 
        'historicalBc', 
        'historicalMd', 
        'historicalOc', 
        'historicalAa', 

        'amip',
        'sst2030',
        'sst2030',
        'sstClim',
        'sstClim4xco2',
        'sstCimAerosol',
        'sstClimSulfate',
        'amip4xco2',
        'amipFuture',
        'aquaControl',
        'aqua4xco2',
        'aqua4K',
        'amip4K',
        ]
experiment_t = ExperimentTranslator()

class FrequencyTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_FREQUENCY
    file_i = None
    component = 'frequency'
    vocab = ['yr', 'mon', 'day', '6hr', '3hr', 'subhr']

    def filename_to_drs(self, context):
        # Read frequency from MIP table
        table = context.drs.table
        variable = context.drs.variable
        if (table is None) or (variable is None):
            raise T.TranslationError('Frequency translation requires table and variable to be known')

        freq = context.table_store.get_variable_attr(table, variable, 'frequency')
        context.drs.frequency = freq

frequency_t = FrequencyTranslator()

#!TODO: Get this information from CMIP tables
class RealmTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_REALM
    file_i = None
    component = 'realm'
    vocab = ['atmos', 'ocean', 'land', 'landIce', 'seaIce', 
                                 'aerosol', 'atmosChem', 'ocnBgchem']

    def filename_to_drs(self, context):
        # Read realm from MIP table
        table = context.drs.table
        variable = context.drs.variable
        if (table is None) or (variable is None):
            raise T.TranslationError('Realm translation requires table and variable to be known')

        realm = context.table_store.get_variable_attr(table, variable, 'modeling_realm')
        context.drs.realm = realm

realm_t = RealmTranslator()

ensemble_t = T.EnsembleTranslator()


variable_t = T.CMORVarTranslator()

version_t = T.VersionTranslator()

subset_t = T.SubsetTranslator()


class CMIP5Translator(T.Translator):

    translators = [activity_t,
                   product_t,
                   model_t,

                   # Must follow model_t
                   institute_t,

                   experiment_t,
                   ensemble_t,
                   variable_t,

                   # Must be processed after variable
                   frequency_t,
                   realm_t,

                   version_t,
                   subset_t,
                   ]

    def init_drs(self, drs=None):
        if drs is None:
            drs = T.DRS()

        drs.activity = 'cmip5'

        return drs


def get_table_store():
    import os
    from glob import glob
    from isenes.drslib.mip_table import MIPTableStore

    tables = []
    table_store = MIPTableStore(config.table_path+'/CMIP5_*')

    return table_store

def make_translator(prefix):
    table_store = get_table_store()
    return CMIP5Translator(prefix, table_store)
