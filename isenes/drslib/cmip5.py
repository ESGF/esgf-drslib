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

CMIP5_DRS = config.CMIP5_DRS


class ProductTranslator(T.GenericComponentTranslator):
    path_i = T.CMIP5_DRS.PATH_PRODUCT
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
        
        # Models used in CMIP3
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
}

#!TODO: Get full list.  This is based on CMIP3
class InstituteTranslator(T.GenericComponentTranslator):
    path_i = T.CMIP5_DRS.PATH_INSTITUTE
    file_i = None
    component = 'institute'
    vocab = model_institution_map.values()

    def filename_to_drs(self, context):
        context.drs.institute = self._deduce_institute(context)

    def drs_to_filepath(self, context):
        if context.drs.institute is None:
            context.drs.institute = self._deduce_institute(context)

        super(InstituteTranslator, self).drs_to_filepath(context)        

    #----

    def _deduce_institute(self, context):
        model = context.drs.model
        if model is None:
            raise T.TranslationError('Institute translation requires model to be known')

        return model_institution_map[model]


institute_t = InstituteTranslator()


#!TODO: Not official identifiers
class ModelTranslator(T.GenericComponentTranslator):
    path_i = T.CMIP5_DRS.PATH_MODEL
    file_i = T.CMIP5_DRS.FILE_MODEL
    component = 'model'
    vocab = model_institution_map.keys()
model_t = ModelTranslator()

class ExperimentTranslator(T.GenericComponentTranslator):
    path_i = T.CMIP5_DRS.PATH_EXPERIMENT
    file_i = T.CMIP5_DRS.FILE_EXPERIMENT
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
        
        # Experiments for CMIP3
        '1pctto2x',  
        '2xco2',
        'pdcntrl',
        'sresa1b',
        '1pctto4x',
        'amip',
        'picntrl', 
        'sresa2',
        '20c3m',
        'commit',
        'slabcntl', 
        'sresb1',
        ]
experiment_t = ExperimentTranslator()

class FrequencyTranslator(T.GenericComponentTranslator):
    path_i = T.CMIP5_DRS.PATH_FREQUENCY
    file_i = None
    component = 'frequency'
    vocab = ['yr', 'mon', 'day', '6hr', '3hr', 'subhr', 'fx']

    def filename_to_drs(self, context):
        context.drs.frequency = self._deduce_freq(context)

    def drs_to_filepath(self, context):
        # If context.drs.frequency is None it could be deduced from the MIP table
        if context.drs.frequency is None:
            context.drs.frequncy = self._deduce_freq(context)

        return super(FrequencyTranslator, self).drs_to_filepath(context)
            
    #----

    def _deduce_freq(self, context):
        # Read frequency from MIP table
        table = context.drs.table
        variable = context.drs.variable
        if (table is None) or (variable is None):
            raise T.TranslationError('Frequency translation requires table and variable to be known')

        return context.table_store.get_variable_attr(table, variable, 'frequency')
        

frequency_t = FrequencyTranslator()

#!TODO: Get this information from CMIP tables
class RealmTranslator(T.GenericComponentTranslator):
    path_i = T.CMIP5_DRS.PATH_REALM
    file_i = None
    component = 'realm'
    vocab = ['atmos', 'ocean', 'land', 'landIce', 'seaIce', 
             'aerosol', 'atmosChem', 'ocnBgchem',
             
             # CMIP3 realms
             'atmosChem', 
             ]

    def filename_to_drs(self, context):
        context.drs.realm = self._deduce_realm(context)

    def drs_to_filepath(self, context):
        # If context.drs.realm is None it could be deduced from the MIP table
        if context.drs.realm is None:
            context.drs.realm = self._deduce_realm(context)

        return super(RealmTranslator, self).drs_to_filepath(context)


    #----

    def _deduce_realm(self, context):
        # Read realm from MIP table
        table = context.drs.table
        variable = context.drs.variable
        if (table is None) or (variable is None):
            raise T.TranslationError('Realm translation requires table and variable to be known')

        return context.table_store.get_variable_attr(table, variable, 'modeling_realm')


realm_t = RealmTranslator()

ensemble_t = T.EnsembleTranslator()


variable_t = T.CMORVarTranslator()

version_t = T.VersionTranslator()

subset_t = T.SubsetTranslator()

class ExtendedTranslator(T.BaseComponentTranslator):
    """
    The extended DRS component is only used when converting DRS->filename.
    It is needed for CMIP3 conversions.
    
    """
    def drs_to_filepath(self, context):
        context.file_parts[T.CMIP5_DRS.FILE_EXTENDED] = context.drs.extended
        
    def path_to_drs(self, context):
        pass
    
    def filename_to_drs(self, context):
        pass
    
extended_t = ExtendedTranslator()

class CMIP5Translator(T.Translator):

    translators = [product_t,
                   model_t,

                   # Must follow model_t
                   institute_t,

                   experiment_t,
                   ensemble_t,
                   variable_t,

                   # Must be processed after variable
                   realm_t,
                   frequency_t,

                   version_t,
                   subset_t,
                   extended_t,
                   ]

    def init_drs(self, drs=None):
        if drs is None:
            drs = T.DRS()

        if drs.activity is None:
            drs.activity = 'cmip5'

        return drs


def get_table_store():
    from isenes.drslib.mip_table import MIPTableStore

    table_store = MIPTableStore(config.table_path+'/CMIP5_*')

    return table_store

def make_translator(prefix):
    table_store = get_table_store()
    return CMIP5Translator(prefix, table_store)




def deduce_variable_details(variable, realm=None, table=None, frequency=None):
    """
    If you know the variable and
    
    """
