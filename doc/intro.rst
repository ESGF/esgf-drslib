============
Introduction
============

Use Cases
=========

The design of the library has been driven by 3 requirements:

1. Deduce the DRS directory structure a DRS-compliant filename. 
2. Validate filenames and directory paths against the DRS.
3. Convert the CMIP3 directory structure into a DRS-compliant form.
4. Manage multiple versions of DRS realm-datasets on the filesystem.


Quick Start
===========

drslib is requires setuptools_ or pip_ for installation.  Download and
install with::

  $ pip install drslib

OR::

  $ easy_install drslib

If you want to download the distribution manually visit drslib's `PyPI page <http://pypi.python.org/pypi/drslib>`_.


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
-------

``drslib`` uses Python's standard logging infrastructure to give
details of it's operation.  Messages are sent to loggers under the
``drslib`` logger.  You can configure logging via metaconfig by
pointing to a separate logging configuration file:

.. code-block:: ini

  [metaconfig]
  configs = drslib
  logging = ~/logging.conf

The format of ``logging.conf`` should conform to the Python logging
`configuration file format`__.  For instance to log warnings to STDERR
you could use the following configuration:

.. code-block:: ini

    [loggers]
    keys=root,drslib
    
    [handlers]
    keys=hand01
    
    [formatters]
    keys=form01
    
    [logger_drslib]
    qualname=drslib
    level=WARN
    handlers=hand01
    
    [logger_root]
    level=NOTSET
    handlers=hand01
    
    [handler_hand01]
    class=StreamHandler
    args=(sys.stderr, )
    formatter=form01
    
    [formatter_form01]
    format=%(asctime)s [%(levelname)s] %(name)s: %(message)s
    datefmt=

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


.. [CMIP5] http://cmip-pcmdi.llnl.gov/cmip5/
.. [DRS] http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf
.. _nose: http://somethingaboutorange.com/mrl/projects/nose
.. _setuptools: http://pypi.python.org/pypi/setuptools
.. _pip: http://pypi.python.org/pypi/pip
.. _NoseXUnit: http://pypi.python.org/pypi/NoseXUnit
