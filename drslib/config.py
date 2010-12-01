# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""


"""

import os

import metaconfig
config = metaconfig.get_config('drslib')

if 'MIP_TABLE_PATH' in os.environ:
    table_path = os.environ['MIP_TABLE_PATH']
else:
    try:
        table_path = config.get('tables', 'path')
    except:
        raise Exception("Please configure your MIP table path using MIP_TABLE_PATH or a config file")

if config.has_option('tables', 'prefix'):
    table_prefix = config.get('tables', 'prefix')
else:
    table_prefix = 'CMIP5_'

if config.has_section('drs'):
    drs_defaults = dict(config.items('drs'))
else:
    drs_defaults = {}


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
# drs_tree command defaults
#

# Default subdirectory of drs-root to scan for incoming files
DEFAULT_INCOMING = 'output'
DEFAULT_MOVE_CMD = 'mv'
try:
    move_cmd = config.get('DEFAULT', 'move-cmd')
except:
    move_cmd = DEFAULT_MOVE_CMD



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
