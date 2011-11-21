# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Code to identify the CMIP5 DRS "product" element based on other DRS elements and selection tables.

Author: Martin Juckes (martin.juckes@stfc.ac.uk)

New in this version:
  1. cmip5_product.status no longer used
  2. additional capability to scan previously published data
  3. option to raise a ProductScopeexception instead of providing 
     "False" return when arguments are inconsistent with selection tables
  4. cmip5_product.rc has a return code on exit -- each return code coming 
     from a unique line of code.

20101004 [0.8]: -- fixed bug which failed on all tables among the special cases.
                -- fixed scan_atomic_dataset to scan only files matching 
                   variable, table, and experiment.  there is an option to
                   turn this of (and scan all files in a directory), 
                   without which the legacy test suite will fail.
20101005 [0.9]: -- fixed code to deal with file time spans not aligned 
                   with calendar years.

"""

import product
import init

# Exception raised by product detection failures
from product import ProductException, cmip5_product, version, version_date
