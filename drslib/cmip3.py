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

import logging
log = logging.getLogger(__name__)

import drslib.translate as T
from drslib.drs import CmipDRS
from drslib.config import CMIP5_DRS, CMIP3_DRS

TranslationError = T.TranslationError


#!NOTE: there is no product component in CMIP3

# From Charlotte's wiki page
instmodel_map = {
    'bcc_cm1': ('CMA', 'BCC-CM1'),
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

class InstituteModelHandler(T.BaseComponentHandler):
    # Dummy value to keep override logic happy.
    component = None

    def path_to_drs(self, context):
        instmodel = context.path_parts[CMIP3_DRS.PATH_INSTMODEL]
        
        try:
            institute, model = instmodel_map[instmodel]
        except KeyError:
            raise TranslationError('CMIP3 Institute/Model identifier %s not recognised' % instmodel)
        
        context.set_drs_component('institute', institute)
        context.set_drs_component('model', model)

    def filename_to_drs(self, context):
        pass
    
instmodel_t = InstituteModelHandler()


class ExperimentHandler(T.GenericComponentHandler):
    path_i = CMIP3_DRS.PATH_EXPERIMENT
    file_i = None
    component = 'experiment'

    def _validate(self, s):
        """
        @note: No validation is done.  Any experiment is accepted
        """
        return s

experiment_t = ExperimentHandler()

class FrequencyHandler(T.BaseComponentHandler):
    vocab = {'yr': 'yr', 'mo': 'mon', 'da': 'day', '3h': '3hr',
             'fixed': 'fx'}
    
    def path_to_drs(self, context):
        cmip3_freq = context.path_parts[CMIP3_DRS.PATH_FREQUENCY]
        try:
            freq = self.vocab[cmip3_freq]
        except KeyError:
            raise TranslationError('CMIP3 frequency %s not recognised' % cmip3_freq)

        context.set_drs_component('frequency', freq)

    def filename_to_drs(self, context):
        pass
    
        
frequency_t = FrequencyHandler()


class RealmHandler(T.GenericComponentHandler):
    path_i = CMIP5_DRS.PATH_REALM
    file_i = None
    component = 'realm'
    # mapping cmip3 realms and variables and realms to cmip5 
    # http://metaforclimate.eu/trac/browser/cmip5q/trunk/CMIP5Outputs_to_Components
    
    # realm_map = {'cmip3Realm': ('CMIP5Realm',),}
    # atmos, ocean, land, landIce, seaIce, aerosol atmosChem, ocnBgchem
    realm_map = {'atm': ('atmos', 'aerosol', 'atmosChem','land'),
                 'ice': ('seaIce',),
                 'land': ('land','landIce'), 
                 'ocn': ('ocean',),
                 }
    # CMIP3 atmos and land variables can map onto 4 different cmip5 realms.  
    # Assume CMIP3 atm variables map onto CMIP5 atmos realm unless they appear in this dictionary 
    var_map={'atmos': {'mrsos': 'land',
                       'trsult': 'aerosol',
                       'trsul': 'aerosol',
                       'tro3': 'atmosChem',
                       },
             'land': {'sftgif': 'landIce',},
             }
                               
    def path_to_drs(self, context):
        cmip3_realm = context.path_parts[CMIP3_DRS.PATH_REALM]
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

realm_t = RealmHandler()

class EnsembleHandler(T.BaseComponentHandler):
    def path_to_drs(self, context):
        r_str = context.path_parts[CMIP3_DRS.PATH_ENSEMBLE]
        mo = re.match(r'run(\d+)', r_str)
        if not mo:
            raise TranslationError('Unrecognised CMIP3 ensemble identifier %s' % r_str)
        
        ensemble = (int(mo.group(1)), None, None)
        context.set_drs_component('ensemble', ensemble)

    def filename_to_drs(self, context):
        pass
            
ensemble_t = EnsembleHandler()


class VariableHandler(T.GenericComponentHandler):
    path_i = CMIP3_DRS.PATH_VARIABLE
    file_i = None
    component = 'variable'

    def filename_to_drs(self, context):
        table = context.file_parts[CMIP3_DRS.FILE_TABLE]
        context.set_drs_component('table', table)

    def _validate(self, s):
        """
        @note: No validation is done.  Any variable  is accepted
        """
        return s

variable_t = VariableHandler()


#!NOTE: No version in CMIP3

#!TODO: Subset translator

class SubsetHandler(T.BaseComponentHandler):
    """
    Subsets are irregular in CMIP3 so we just extract the irregular bit
    and put it in DRS.extended.
    
    """
    def filename_to_drs(self, context):
        extended = context.file_parts[CMIP3_DRS.FILE_EXTENDED]
        context.set_drs_component('extended', extended)
        
    def path_to_drs(self, context):
        pass
    
subset_t = SubsetHandler()

class FnFixHandler(T.BaseComponentHandler):
    """
    Fix problem filenames in the DRS structure.

    """
    def drs_to_filepath(self, context):
        pass
        
    def path_to_drs(self, context):
        pass
    
    def filename_to_drs(self, context):
        # Detect variables containing underscores and fix.
        varbits = context.drs.variable.split('_')
        if len(varbits) > 1 and context.drs.table == varbits[-1]:
            extbits = context.drs.extended.split('_')
            #context.drs.variable = '_'.join(varbits[:-1])
            context.drs.table = extbits[0]
            context.drs.extended = '_'.join(extbits[1:])

            log.warn(('Variable containing underscore detected'
                      +'Setting variable=%s, table=%s, extended=%s')
                     % (context.drs.variable,
                        context.drs.table,
                        context.drs.extended))
                     

fnfix_t = FnFixHandler()

class CMIP3TranslatorContext(T.TranslatorContext):
    """
    A customised context class for converting CMIP3 paths

    CMIP3 filenames are irregular so we need to override some behaviour of
    TranslatorContext.
    
    """

    #!FIXME: This regular expression doesn't allow underscores in variable
    #        names.  Unfortunately CMIP3 has them.
    _fnrexp = re.compile(r'([a-zA-Z0-9]+)_([a-zA-Z0-9]+)(?:[._-](.*))?.nc$')
    
    _override = set()

    def __init__(self, filename=None, path=None, drs=None, table_store=None):
        assert table_store is None
        
        if path is None:
            self.path_parts = [None] * 10
        else:
            self.path_parts = path.split('/')
    
        self.file_parts = [None] * 7
        if filename is not None:
            # CMIP3 requires different filename parsing
            mo = self._fnrexp.match(filename)
            if not mo:
                raise TranslationError('Unrecognised CMIP3 filename %s' % filename)
            self.file_parts[CMIP3_DRS.PATH_VARIABLE] = mo.group(1)
            self.file_parts[CMIP3_DRS.FILE_TABLE] = mo.group(2)
            self.file_parts[CMIP3_DRS.FILE_EXTENDED] = mo.group(3)
            
        if drs is None:
            self.drs = CmipDRS()
        else:
            self.drs = drs

class CMIP3Translator(T.Translator):
    
    ContextClass = CMIP3TranslatorContext

    handlers = [instmodel_t,
                experiment_t,
                ensemble_t,
                variable_t,
                
                # Must be processed after variable
                realm_t,
                frequency_t,
                subset_t,
                
                # Fix some unusual CMIP3 filenames
                fnfix_t,
                ]

    def init_drs(self, drs=None):
        if drs is None:
            drs = CmipDRS()

        drs.activity = 'cmip3'
        drs.version = 1
        drs.product = 'output'

        return drs


def make_translator(prefix):
    return CMIP3Translator(prefix)

