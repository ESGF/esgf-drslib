.. drslib documentation master file, created by
   sphinx-quickstart on Thu Jul  8 11:22:21 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


esgf-drslib documentation
=========================


Drslib is a Python library for processing data intended for publishing
into the Earth System Grid Federation (`ESGF`_).  It was first
designed for the 5th Climate Model Intercomparison Project (CMIP5_)
Data Reference Syntax (DRS_).  It has subsequently been extended to
support the SPECS_ and CORDEX_ projects and provides an internal API
for future extension.  Drslib API-level code for working with DRS
components, algorithms for decuding DRS components from incomplete
information and a command-line tool for manipulating data files into
the recommended DRS directory structure.It has been developed by the
`Centre for Environmental Data Archival <http://ceda.ac.uk>`_ as part
of the ESG Federation.

.. _CMIP5: http://cmip-pcmdi.llnl.gov/cmip5/
.. _DRS: http://cmip-pcmdi.llnl.gov/cmip5/docs/cmip5_data_reference_syntax.pdf
.. _ESGF: http://esgf.org/
.. _CORDEX: http://wcrp-cordex.ipsl.jussieu.fr/
.. _SPECS: http://www.specs-fp7.eu/


User Guide
----------

.. toctree::
   :maxdepth: 3

   intro.rst
   howto.rst
   command.rst
   product.rst
   schemes.rst

Reference
---------

.. toctree::
   :maxdepth: 3

   modules.rst

Appendix
--------

.. toctree::
   :maxdepth: 3

   cmip3.rst


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

