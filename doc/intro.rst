============
Introduction
============

This is a Python library for processing the 5th Climate Model
Intercomparison Project [CMIP5]_ Data Reference Syntax [DRS]_.

Use Cases
=========

The design of the library has been driven by 3 requirements:

1. Deduce the DRS directory structure a DRS-compliant filename. 
2. Validate filenames and directory paths against the DRS.
3. Convert the CMIP3 directory structure into a DRS-compliant form.
4. Manage multiple versions of DRS realm-datasets on the filesystem.

Installing
==========

drslib requires setuptools_ for installation.  You can run
easy_install directly on the tarball::

  $ easy_install drslib*.tar.gz

Quick Start
===========

See the ``examples`` directory and ``translate_cmip3.py``.

Configuration
=============

``drslib`` requires the CMIP5 MIP tables to be available in
order to run.  You can point to your MIP table location using the
environment variable ``MIP_TABLE_PATH``.  All tables should be named
``CMIP5_*``.

Alternatively you can use metaconfig_ to configure the location of
your MIP tables.  Create the following in your ``$HOME/.metaconfig.conf`` file:

.. code-block:: ini

  [metaconfig]
  configs = drslib

  [drslib:tables]
  tables = /path/to/mip/tables
  model_table = /path/to/model_table

.. _metaconfig: http://pypi.python.org/pypi/metaconfig

The option ``model_table`` is optional and if specified should point
to the "CMIP5 Modelling Group" spreadsheet in CSV format.  This table
is used to map model names to institute names.  The drslib package is
distributed with a recent version of this file.

Default DRS attributes used by the ``drs_tree`` command can be set in
the ``drs`` section:

.. code-block:: ini

  [drslib:drs]
  root = /path/to/drs/activity
  institute = MOHC
  model = HadCM3


Testing
=======

drslib ships with a test suite compliant with nose_.  The suite
can be run in various ways:

Run all tests::

  $ nosetests

Run core tests via setuptools::

  $ python setup.py test

Run doctest scripts in the examples directory

  $ nosetests examples

.. [CMIP5] http://cmip-pcmdi.llnl.gov/cmip5/
.. [DRS] http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf
.. _nose: http://somethingaboutorange.com/mrl/projects/nose
.. _setuptools: http://pypi.python.org/pypi/setuptools
