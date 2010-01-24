# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
A translator specific to CMIP3

The CMIP3 translation code is less complete than CMIP5.  It focuses
on translating paths to DRS instances.  

 1. CMIP3 files or paths cannot be generated from DRS instances
 2. the code doesn't use MIP tables to validate and deduce components

"""

import re

import isenes.drslib.translate as T
import isenes.drslib.config as config

TranslationError = T.TranslationError

DRS_PATH_ACTIVITY = 0
DRS_PATH_INSTMODEL = 5
DRS_PATH_EXPERIMENT = 1
DRS_PATH_FREQUENCY = 3
DRS_PATH_REALM = 2
DRS_PATH_VARIABLE = 4
DRS_PATH_ENSEMBLE = 6

DRS_FILE_VARIABLE = 0
DRS_FILE_TABLE = 1
DRS_FILE_SUBSET = 2


#!NOTE: there is no product component in CMIP3

# From Charlotte's wiki page
instmodel_map = {
    'bccr_bcm2_0': ('BCCR', 'BCM2'), 
    'cccma_cgcm3_1': ('CCCMA', 'CGCM3-1-T47'),     
    'cccma_cgcm3_1_t63': ('CCCMA','CGCM3-1-T63'),
    'cnrm_cm3': ('CNRM','CM3'),
    'miub_echo_g': ('MIUB-KMA','ECHO-G'),
    'csiro_mk3_0': ('CSIRO','MK3'),
    'csiro_mk3_5': ('CSIRO','MK3-5'),
    'gfdl_cm2_0': ('GFDL','CM2'),
    'gfdl_cm2_1': ('GFDL','CM2-1'),
    'inmcm3_0': ('INM','CM3'),
    'ipsl_cm4': ('IPSL','CM4'),
    'iap_fgoals1_0_g': ('LASG','FGOALS-G1-0'),
    'mpi_echam5': ('MPIM','ECHAM5'),
    'mri_cgcm2_3_2a': ('MRI','CGCM2-3-2'),
    'giss_aom': ('NASA','GISS-AOM'),
    'giss_model_e_h': ('NASA','GISS-EH'),
    'giss_model_e_r': ('NASA','GISS-ER'),
    'ncar_ccsm3_0': ('NCAR','CCSM3'),
    'ncar_pcm1': ('NCAR','PCM'),
    'miroc3_2_hires': ('NIES','MIROC3-2-HI'),
    'miroc3_2_medres': ('NIES','MIROC3-2-MED'),
    'ukmo_hadcm3': ('UKMO','HADCM3'),
    'ukmo_hadgem1': ('UKMO','HADGEM1'),
    'ingv_echam4': ('INGV','ECHAM4'), 
}

class InstituteModelTranslator(T.BaseComponentTranslator):
    def path_to_drs(self, context):
        instmodel = context.path_parts[DRS_PATH_INSTMODEL]
        
        try:
            institute, model = instmodel_map[instmodel]
        except KeyError:
            raise TranslationError('CMIP3 Institute/Model identifier %s not recognised' % instmodel)
        
        context.set_drs_component('institute', institute)
        context.set_drs_component('model', model)

    def filename_to_drs(self, context):
        pass
    
instmodel_t = InstituteModelTranslator()


class ExperimentTranslator(T.GenericComponentTranslator):
    path_i = DRS_PATH_EXPERIMENT
    file_i = None
    component = 'experiment'

    def _validate(self, s):
        """
        @note: No validation is done.  Any experiment is accepted
        """
        return s

experiment_t = ExperimentTranslator()

class FrequencyTranslator(T.BaseComponentTranslator):
    vocab = {'yr': None, 'mo': 'mon', 'da': 'day', '3h': '3hr',
             'fixed': 'fx'}
    
    def path_to_drs(self, context):
        cmip3_freq = context.path_parts[DRS_PATH_FREQUENCY]
        try:
            freq = self.vocab[cmip3_freq]
        except KeyError:
            raise TranslationError('CMIP3 frequency %s not recognised' % cmip3_freq)

        context.set_drs_component('frequency', freq)

    def filename_to_drs(self, context):
        pass
    
        
frequency_t = FrequencyTranslator()


class RealmTranslator(T.GenericComponentTranslator):
    path_i = T.DRS_PATH_REALM
    file_i = None
    component = 'realm'
    #mapping cmip3 realms and variables and realms to cmip5 
    #http://metaforclimate.eu/trac/browser/cmip5q/trunk/CMIP5Outputs_to_Components
    
    #realm_map = {'cmip3Realm': ('CMIP3Realm',),}
    #atmos, ocean, land, landIce, seaIce, aerosol atmosChem, ocnBgchem
    realm_map = {'atm': ('atmos', 'aerosol', 'atmosChem','land'),
                            'ice': ('seaIce',),
                            'land': ('land','landIce'), 
                            'ocn': ('ocean',),
                            }
    #CMIP3 atmos variables can map onto 4 different cmip5 realms.  
    #The atmos_map dictionary defines this mapping
    #Assume CMIP3 atm variables map onto CMIP5 atmos realm unless they appear in this dictionary 
    var_map={'atmos': {'mrsos': ('land',),
                              'trsult': ('aerosol',),
                              'trsul': ('aerosol',),
                              'tro3': ('atmoschem',),
                              },
             'land': {'sftgif': ('landIce',),}
             }
                               
    def path_to_drs(self, context):
        cmip3_realm = context.path_parts[DRS_PATH_REALM]
        try:
            realm_list = self.realm_map[cmip3_realm]
        except KeyError:
            raise TranslationError('CMIP3 realm %s not recognised' % cmip3_realm)
        
        realm = realm_list[0]
        if len(realm_list) > 1:
            variable = context.drs.variable
            if variable is None:
                raise TranslationError('CMIP3 realm %s cannot be deduced without variable' % cmip3_realm)
            
            # Realm is replaced if it's in var_map
            try:
                realm = self.var_map[realm][variable]
            except KeyError:
                pass

        context.set_drs_component('realm', realm)

realm_t = RealmTranslator()

#!TODO: EnsembleTranslator
class EnsembleTranslator(T.BaseComponentTranslator):
    def path_to_drs(self, context):
        r_str = context.path_parts[DRS_PATH_ENSEMBLE]
        mo = re.match(r'run(\d+)', r_str)
        if not mo:
            raise TranslationError('Unrecognised CMIP3 ensemble identifier %s' % r_str)
        
        context.set_drs_component('ensemble', int(mo.group(1)))

    def filename_to_drs(self, context):
        pass
            
ensemble_t = EnsembleTranslator()


class VariableTranslator(T.GenericComponentTranslator):
    path_i = DRS_PATH_EXPERIMENT
    file_i = None
    component = 'variable'

    def filename_to_drs(self, context):
        table = context.file_parts[DRS_FILE_TABLE]
        context.set_drs_component('table', table)

    def _validate(self, s):
        """
        @note: No validation is done.  Any variable  is accepted
        """
        return s

variable_t = VariableTranslator()


#!NOTE: No version in CMIP3

#!TODO: Subset translator
#subset_t = T.SubsetTranslator()


class CMIP3Translator(T.Translator):

    translators = [instmodel_t,
                   experiment_t,
                   ensemble_t,
                   variable_t,

                   # Must be processed after variable
                   realm_t,
                   frequency_t,
                   #subset_t,
                   ]

    def init_drs(self, drs=None):
        if drs is None:
            drs = T.DRS()

        drs.activity = 'cmip3'
        drs.version = 1
        drs.product = 'output'

        return drs


def make_translator(prefix):
    return CMIP3Translator(prefix)

