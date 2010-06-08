# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Central configuration module

"""

import os

if 'MIP_TABLE_PATH' in os.environ:
    table_path = os.environ['MIP_TABLE_PATH']
else:
    table_path = os.path.join(os.path.dirname(__file__), 'cmip5_tables')

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

