# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.
"""
Test the translate_cmip3 script

"""

import os, sys, shutil
import tempfile

from unittest import TestCase

from gen_drs import write_listing
from drslib.translate_cmip3 import main as script_main

import logging

class LogLevelAssertionError(Exception):
    def __init__(self, msg, record):
        super(LogLevelAssertionError, self).__init__(msg)
        self.record = record

class AssertLevelFilter(logging.Filter):
    """
    Assert messages match certain levels
    """
    def __init__(self, lessthan=logging.WARNING):
        self.lessthan = lessthan

    def filter(self, record):
        if not record.levelno < self.lessthan:
            raise LogLevelAssertionError("Level exceeded", record)
        
        return True

class TestNewBatch(TestCase):
    """
    Test processing of the batch that was originally missed.

    """
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='translate_cmip3-')
        listing = os.path.join(os.path.dirname(__file__), 'cmip3_new.ls')
        self.src_dir = os.path.join(self.tmpdir, 'src')
        self.dst_dir = os.path.join(self.tmpdir, 'dst')
        write_listing(self.src_dir, listing)

        self.log_filter = AssertLevelFilter()
        self.script_logger = logging.getLogger('drslib.translate_cmip3')
        self.script_logger.addFilter(self.log_filter)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        self.script_logger.removeFilter(self.log_filter)

    def test1(self):
        cmd = 'translate_cmip3 -l WARNING -d %s %s' % (self.src_dir, self.dst_dir)
        script_main(cmd.split())
