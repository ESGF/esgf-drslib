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

#!TODO: Get full list.  This is based on CMIP3
class InstituteTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_INSTITUTE
    file_i = None
    component = 'institute'
    vocab = ['BCCR', 'CCMA', 'CNRM', 'MIUB-KMA', 'CSIRO',
             'GFDL', 'INM', 'IPSL', 'LASG', 'MPIM', 'MRI',
             'NASA', 'NCAR', 'NIES', 'UKMO', 'INGV'
             ]
institute_t = InstituteTranslator()

#!TODO: Not official identifiers
class ModelTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_MODEL
    file_i = T.DRS_FILE_MODEL
    component = 'model'
    vocab = [
        'NorESM', 'MRI-CGCM3', 'MRI-ESM1', 'MRI-AM20km',
        'MRI-AM60km', 'MIROC4.2M', 'MIROC4.2H', 'MIROC3.2M',
        'MIROC-ESM', 'IPSL-CM6', 'IPSL-CM5', 'INMCM4.0',
        'HiGEM1.2', 'HadGEM2-ES', 'HadGEM2-AO', 'HadCM3Q',
        'HadCM3', 'GFDL-HIRAM', 'GFDL-ESM2G', 'GFDL-ESM2M',
        'GFDL-CM3', 'GFDL-CM2.1', 'FGOALS-S2.0', 'FGOALS-G2.0',
        'FGOALS-gl', 'ECHAM5-MPIOM', 'CSIRO-Mk3.5A', 'CCSM4H',
        'CCSM4M', 'CNRM-CM5', 'CanESM2', 'ACCESS', 'BCC-CSM',
        ]
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
frequency_t = FrequencyTranslator()

#!TODO: Get this information from CMIP tables
class RealmTranslator(T.GenericTranslator):
    path_i = T.DRS_PATH_REALM
    file_i = None
    component = 'realm'
    vocab = ['atmos', 'ocean', 'land', 'landIce', 'seaIce', 
                                 'aerosol', 'atmosChem', 'ocnBgchem']
realm_t = RealmTranslator()

ensemble_t = T.EnsembleTranslator()

def get_table_store():
    import os
    from glob import glob
    from isenes.drslib.mip_table import MIPTableStore

    tables = []
    table_store = MIPTableStore(config.table_path+'/CMIP5_*')

    return table_store

# Build VariableTranslator from MIP tables
def make_vartranslator():
    table_store = get_table_store()

    return T.CMORVarTranslator(table_store.tables.values())

variable_t = make_vartranslator()

version_t = T.VersionTranslator()

subset_t = T.SubsetTranslator()


class CMIP5Translator(T.Translator):

    translators = [activity_t,
                   product_t,
                   institute_t,
                   model_t,
                   experiment_t,
                   frequency_t,
                   realm_t,
                   ensemble_t,
                   variable_t,
                   version_t,
                   subset_t,
                   ]

    def init_drs(self, drs=None):
        if drs is None:
            drs = T.DRS()

        drs.activity = 'cmip5'

        return drs

