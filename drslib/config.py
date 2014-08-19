# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""


"""

#!TODO: tidy this up and review what needs documenting.

import os

import metaconfig
config = metaconfig.get_config('drslib')

##############################################################################
# Configure the location of MIP tables.  
# 
# This can be configured with the MIP_TABLE_PATH environment varliable
# or in the drslib metaconfig as 
# [drslib:tables]
# path = $MIP_TABLE_PATH
#
# You can override the location of CSV versions of the tables with the 
# "path_csv" option in metaconfig.  You can override the prefix of tables
# with the "prefix" option.
#

if 'MIP_TABLE_PATH' in os.environ:
    table_path = os.environ['MIP_TABLE_PATH']
else:
    try:
        table_path = config.get('tables', 'path')
    except:
        raise Exception("Please configure your MIP table path using MIP_TABLE_PATH or a config file")

try:
    table_path_csv = config.get('tables', 'path_csv')
except:
    table_path_csv = '%s_csv' % os.path.normpath(table_path)

# Check both paths exist
if not os.path.exists(table_path):
    raise Exception("The configured mip-table path %s does not exist" % table_path)
if not os.path.exists(table_path_csv):
    raise Exception("The mip-table CSV directory %s could not be found" % table_path_csv)


if config.has_option('tables', 'prefix'):
    table_prefix = config.get('tables', 'prefix')
else:
    table_prefix = 'CMIP5_'

##############################################################################
# Configure site-specific drs vocabulary behaviour
#

#
# Configure default values of the drs attributes
#
#!TODO: this should probably be drs_defaults.  Requires major version change. 
drs_defaults = {}
if config.has_section('drs'):
    for key, value in config.items('drs'):
        if '_' in value:
            #!TODO: expand to fully test for allowed characters
            raise Exception('Forbidden character in drs default %s=%s' % (key, value))
        drs_defaults[key] = value



#
# Configure the model table.  You shouldn't need to change this from the
# internal default.
#
#!TODO: Check whether this is used.
try:
    model_table = config.get('tables', 'model_table')
except:
    model_table = os.path.join(os.path.dirname(__file__), 'data', 
                               'CMIP5_models.csv')

#
# Allow backward compatibility with the original version system
# Original behaviour is default
#
try:
    version_by_date = config.getboolean('versioning', 'version_by_date')
except:
    version_by_date = True

#
# Allow override of experiment names.  
# These are merged with names in the MIP tables
#
try:
    experiments = config.get('vocabularies', 'experiments').split()
except:
    experiments = []

#
# Allow override of institute and model names
#
institutes = {}
try:
    institute_map = config.get('vocabularies', 'institutes')
except:
    pass
else:
    for line in institute_map.split('\n'):
        line = line.strip()
        if line:
            institute, models = line.split(':')
            institutes[institute] = models.strip().split()


##############################################################################
# drs_tree command defaults
#

# Default subdirectory of drs-root to scan for incoming files
DEFAULT_INCOMING = 'output'
DEFAULT_MOVE_CMD = 'mv'
#!FIXME: s/move-cmd/move_cmd/
try:
    move_cmd = config.get('DEFAULT', 'move-cmd')
except:
    move_cmd = DEFAULT_MOVE_CMD

##############################################################################
# Mapfile generation checksum hook
#

try:
    checksum_func_str = config.get('DEFAULT', 'checksum_func')
except:
    checksum_func = None
else:
    #!TODO: Move this into metaconfig
    package_name, callable_name = checksum_func_str.split(':')
    # This is the easiest way of looking inside a package
    __import__(package_name)
    module = sys.modules[package_name]
    checksum_func = module.getattr(callable_name)
    if not callable(checksum_func):
        raise ValueError("checksum_func %s:%s is not callable" % (package_name, callable_name))


##############################################################################
# DRS Schemes
# Each scheme maps a scheme name to a DRSFileSystem instance

#!TODO: it would probably be better not to have to do the local import here.
def get_drs_scheme(key):
    from drslib.cmip5 import CMIP5FileSystem
    from drslib.cordex import CordexFileSystem
    from drslib.specs import SpecsFileSystem

    drs_schemes = {
        'cmip': CMIP5FileSystem,
        'cordex': CordexFileSystem,
        'specs': SpecsFileSystem,
        }

    return drs_schemes[key]

default_drs_scheme = 'cmip'
drs_schemes = ['cmip', 'cordex', 'specs']
    
##############################################################################
# Check/repair options
#

# Should we only check the latest version?
check_latest = True

#
# CMIP3 component to file/path position mapping
#

class CMIP3_DRS:
    PATH_INSTMODEL = 4
    PATH_EXPERIMENT = 0
    PATH_FREQUENCY = 2
    PATH_REALM = 1
    PATH_VARIABLE = 3
    PATH_ENSEMBLE = 5

    FILE_VARIABLE = 0
    FILE_TABLE = 1
    #FILE_SUBSET = 2
    FILE_EXTENDED = 6

#
# CMIP5 component to file/path position mapping
#

class CMIP5_DRS:
    PATH_PRODUCT = 0
    PATH_INSTITUTE = 1
    PATH_MODEL = 2
    PATH_EXPERIMENT = 3
    PATH_FREQUENCY = 4
    PATH_REALM = 5
    PATH_TABLE = 6
    PATH_ENSEMBLE = 7
    PATH_VERSION = 8
    PATH_VARIABLE = 9
    
    FILE_VARIABLE = 0
    FILE_TABLE = 1
    FILE_MODEL = 2
    FILE_EXPERIMENT = 3
    FILE_ENSEMBLE = 4
    FILE_SUBSET = 5
    FILE_EXTENDED = 6


#
# CMIP5 component to file/path position mappings for DRS <= v0.27
#

class CMIP5_DRS_OLD:
    PATH_PRODUCT = 0
    PATH_INSTITUTE = 1
    PATH_MODEL = 2
    PATH_EXPERIMENT = 3
    PATH_FREQUENCY = 4
    PATH_REALM = 5
    PATH_VERSION = 6
    PATH_VARIABLE = 7
    PATH_ENSEMBLE = 8
    
    FILE_VARIABLE = 0
    FILE_TABLE = 1
    FILE_MODEL = 2
    FILE_EXPERIMENT = 3
    FILE_ENSEMBLE = 4
    FILE_SUBSET = 5
    FILE_EXTENDED = 6

# Without version!
class CMIP5_CMOR_DRS:
    PATH_PRODUCT = 0
    PATH_INSTITUTE = 1
    PATH_MODEL = 2
    PATH_EXPERIMENT = 3
    PATH_FREQUENCY = 4
    PATH_REALM = 5
    PATH_VARIABLE = 6
    PATH_ENSEMBLE = 7
    
    FILE_VARIABLE = 0
    FILE_TABLE = 1
    FILE_MODEL = 2
    FILE_EXPERIMENT = 3
    FILE_ENSEMBLE = 4
    FILE_SUBSET = 5
    FILE_EXTENDED = 6
