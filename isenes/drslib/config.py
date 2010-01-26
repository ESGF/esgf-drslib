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

table_path = os.path.join(os.path.dirname(__file__), 'cmip5_tables')

#
# CMIP3 component to file/path position mapping
#

class CMIP3_DRS:
    PATH_ACTIVITY = 0
    PATH_INSTMODEL = 5
    PATH_EXPERIMENT = 1
    PATH_FREQUENCY = 3
    PATH_REALM = 2
    PATH_VARIABLE = 4
    PATH_ENSEMBLE = 6

    FILE_VARIABLE = 0
    FILE_TABLE = 1
    #FILE_SUBSET = 2
    FILE_EXTENDED = 6

#
# CMIP5 component to file/path position mapping
#

class CMIP5_DRS:
    PATH_ACTIVITY = 0
    PATH_PRODUCT = 1
    PATH_INSTITUTE = 2
    PATH_MODEL = 3
    PATH_EXPERIMENT = 4
    PATH_FREQUENCY = 5
    PATH_REALM = 6
    PATH_VARIABLE = 7
    PATH_ENSEMBLE = 8
    PATH_VERSION = 9
    
    FILE_VARIABLE = 0
    FILE_TABLE = 1
    FILE_MODEL = 2
    FILE_EXPERIMENT = 3
    FILE_ENSEMBLE = 4
    FILE_SUBSET = 5
    FILE_EXTENDED = 6

