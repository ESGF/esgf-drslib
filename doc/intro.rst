============
Introduction
============


Use Cases
=========

The design of the library has been driven by the following requirements:

1. Deduce the DRS directory structure a DRS-compliant filename. 
2. Validate filenames and directory paths against the DRS.
3. Convert the CMIP3 directory structure into a DRS-compliant form.
4. Manage multiple versions of DRS publication-level datasets on the filesystem.
5. Detect the CMIP5 product DRS component during data publication.


Installation
============

drslib is written in Python_.  It requires one of the installation
tools setuptools_ or pip_.  Other requirements are downloaded
automatically during installation.  Download and install with:

.. code-block:: bash

  # Using pip
  $ pip install drslib

  # OR using setuptools
  $ easy_install drslib

If you are upgrading drslib you will need to add the "-U" option to
either pip or easy_install.

.. pull-quote::

  **Note:** To install onto an ESG datanode you can use use the
  ``easy_install`` in ``/usr/local/cdat/bin``.  This will install
  ``drslib`` into ``/usr/local/cdat/bin/python`` and install
  ``drs_tool`` as ``/usr/local/cdat/bin/drs_tool``.




Installing for development
--------------------------

If you want to inspect the code you will need to get the source
distribution. Either visit drslib's `PyPI page
<http://pypi.python.org/pypi/drslib>`_ and follow the download link or
clone the git repository esgf-drslib.git_.  You can also view the
evolution of the project on esgf's gitweb__.

Once you have unpacked the tarball you must activate the distribution
in `develop` mode.  To do this execute the following using a python
interpreter with setuptools_ installed:

.. code-block:: bash

  $ python setup.py develop

__ esgf-drslib.gitweb_


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

Default DRS attributes used by the ``drs_tool`` command can be set in
the ``drs`` section:

.. code-block:: ini

  [drslib:drs]
  root = /path/to/drs/activity
  institute = MOHC
  model = HadCM3

It is usually convenient to set at least ``root`` and ``activity`` in
the configuration file.

Logging
=======

``drslib`` uses Python's standard logging infrastructure to give
details of it's operation.  Messages are sent to loggers under the
``drslib`` logger.  You can configure logging via metaconfig by
pointing to a separate logging configuration file:

.. code-block:: ini

  [metaconfig]
  configs = drslib
  logging = ~/logging.conf

The format of ``logging.conf`` should conform to the Python logging
`configuration file format`__.  An example logging configuration is
given below which will log product detection decisions separately from
general drslib warnings:

.. code-block:: ini

   #
   # Basic logging configuration for drs_tool
   #
   # This configuration prints product detection decisions to STDERR and logs
   # warnings to ./drs_tool.log
   #

   [loggers]
   keys=root,drslib,p_cmip5

   [handlers]
   keys=drslib_h,p_cmip5_h

   [formatters]
   keys=f1,f2

   #---------------------------------------------------------------------------
   # Loggers

   # No catch-all logging
   [logger_root]
   handlers=
   level=NOTSET

   [logger_drslib]
   qualname=drslib
   handlers=drslib_h

   [logger_p_cmip5]
   qualname=drslib.p_cmip5
   handlers=p_cmip5_h
   propagate=0

   #---------------------------------------------------------------------------
   # Handlers & Formatters

   [handler_drslib_h]
   class=FileHandler
   args=('./drs_tool.log', )
   formatter=f1
   level=INFO

   [handler_p_cmip5_h]
   class=StreamHandler
   args=(sys.stderr, )
   formatter=f2
   level=INFO

   [formatter_f1]
   format=%(asctime)s [%(levelname)s] %(name)s: %(message)s
   datefmt=

   [formatter_f2]
   format=[%(levelname)s] %(name)s: %(message)s
                                                                        

__ http://docs.python.org/library/logging.html#configuration-file-format



Testing
=======

drslib ships with a test suite compliant with nose_.  The suite can be
run in various ways.  The test suite uses the extension NoseXUnit_ to
produce XML reports of the test results.  NoseXUnit will be
automatically installed if you run the tests via ``setup.py``::

  $ python setup.py test

Or if the depencencies are satisfied you can run all tests with::

  $ nosetests


Reporting Bugs
==============

The drslib bugtracker is available on `esgf.org bugzilla`_.

* `Submit a bug here <http://esgf.org/bugzilla/enter_bug.cgi?product=drslib>`_.

.. _CMIP5: http://cmip-pcmdi.llnl.gov/cmip5/
.. _DRS: http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf
.. _nose: http://somethingaboutorange.com/mrl/projects/nose
.. _setuptools: http://pypi.python.org/pypi/setuptools
.. _pip: http://pypi.python.org/pypi/pip
.. _NoseXUnit: http://pypi.python.org/pypi/NoseXUnit
.. _esgf-drslib.git: http://esgf.org/git/esgf-drslib.git
.. _esgf-drslib.gitweb: http://esgf.org/gitweb/?p=esgf-drslib.git;a=summary
.. _CEDA: http://www.ceda.ac.uk
.. _`Stephen Pascoe`: mailto:Stephen.Pascoe@stfc.ac.uk
.. _Python: http://www.python.org
.. _`esgf.org bugzilla`: http://esgf.org/bugzilla/enter_bug.cgi?product=drslib
