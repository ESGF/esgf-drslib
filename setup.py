# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import setup, find_packages
import sys, os

version = '0.1.9'
drs_version = '0.24'
cmor2_version = '2.0'

setup(name='drslib',
      version=version,
      description="A library for processing the CMIP5 Data Reference Syntax",
      long_description="""\

This library supports the generation of paths and filenames
corresponding to version %(drs_version)s of the CMIP Data Reference
Syntax [DRS]_.  MIP table support is based on CMOR-%(cmor2_version)s.

.. [DRS] http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf

""" % globals(),
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Stephen Pascoe',
      author_email='Stephen.Pascoe@stfc.ac.uk',
      url='',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'test']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'metaconfig',
      ],
      entry_points= {
        'console_scripts': ['translate_cmip3 = drslib.translate_cmip3:main',
                            'drs_tree = drslib.drs_command:main'],
        },
      test_suite='nose.collector',
      )
