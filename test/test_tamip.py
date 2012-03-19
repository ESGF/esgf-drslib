# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os

from drslib import cmip5, mip_table

TAMIP_TEST_PATH = os.path.join(os.path.dirname(__file__), 'TAMIP')

table_store = mip_table.MIPTableStore('%s/TAMIP_*' % TAMIP_TEST_PATH)
translator = cmip5.make_translator('tamip', table_store=table_store)

def test_gen_1():
    fh = open(os.path.join(TAMIP_TEST_PATH, 'tamip.ls'))
    for filename in fh:
        yield do, filename

def do(filename):
    drs = translator.filename_to_drs(filename)
    
    drs.version = 1
    drs.product = 'output'
    drs.activity == 'tamip'

    print drs
    assert drs.is_complete()
