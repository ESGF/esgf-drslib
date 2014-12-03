===========
DRS Schemes
===========

In order to support multiple projects beyond CMIP5, DRSlib has been extended to support multiple DRS schemes.  The ``--scheme`` switch to ``drs_tool`` will allow you to select form a set of configured schemes, currently:

 1. CMIP5 (default)
 2. SPECS
 3. CORDEX

Each scheme has a different set of DRS components and component ordering.

When operating on projects other than CMIP5 drslib is designed to
perform less metadata checks.  These functions are now performed by
drslib's sister tool `ceda-cc`_.  The ``ceda_cc`` tool will verify
files meet a project's metadata requirements and output a JSON file
which can be used by drslib to deduce certain metadata values that are
not apparent from the files.  This JSON file is passed to ``drs_tool``
using the `--json-drs` option.

.. _`ceda-cc`: https://pypi.python.org/pypi/ceda-cc
