``drs_tool`` command-line interface
===================================

The ``drs_tool`` command can be used to invoke functions from the
:mod:`drslib.drs_tree` API.  The tool is designed to help ESGF
datanode managers to 

 1. Prepare incoming data for publication, placing files in the DRS
 directory structure.  
 
 2. Manage multiple versions of publication-level datasets to minimise
 disk usage.

 3. Deduce the CMIP5 product into which data should be published
 according to the rules definied in the CMIP5 experiment definition.


Concepts
--------

DRS root 
  The root of the published DRS directory tree.  This is synonimous
  with the directory representing the DRS activity component.

incoming directory
  The directory scanned for data files to be added to the DRS 
  directory tree.  This directory is scanned recursively to find NetCDF 
  files in the DRS filename encoding.  It defaults to ``<drs-root>/output``
  for compatibility with the output structure of CMOR2.  The directory names
  under the incoming directory are not taken into account when deducing 
  the DRS components of files.

DRS pattern
  Each invocation of ``drs_tool`` is given a set of DRS component 
  values that define the portion of the DRS space on which it acts.


Usage
-----

Usage: drs_tool [command] [options] [drs-pattern]

command:
  list            list publication-level datasets
  todo            show file operations pending for the next version
  upgrade         make changes to the selected datasets to upgrade to the next version.
  mapfile         make a mapfile of the selected dataset
  history         list all versions of the selected dataset

drs-pattern:
  A dataset identifier in '.'-separated notation using '%' for wildcards


Options:
  -h, --help            show this help message and exit
  -R ROOT, --root=ROOT  Root directory of the DRS tree
  -I INCOMING, --incoming=INCOMING
                        Incoming directory for DRS files.  Defaults to
                        <root>/output
  -a ACTIVITY, --activity=ACTIVITY
                        Set DRS attribute activity for dataset discovery
  -p PRODUCT, --product=PRODUCT
                        Set DRS attribute product for dataset discovery
  -i INSTITUTE, --institute=INSTITUTE
                        Set DRS attribute institute for dataset discovery
  -m MODEL, --model=MODEL
                        Set DRS attribute model for dataset discovery
  -e EXPERIMENT, --experiment=EXPERIMENT
                        Set DRS attribute experiment for dataset discovery
  -f FREQUENCY, --frequency=FREQUENCY
                        Set DRS attribute frequency for dataset discovery
  -r REALM, --realm=REALM
                        Set DRS attribute realm for dataset discovery
  -v VERSION, --version=VERSION
                        Force version upgrades to this version
  -P FILE, --profile=FILE
                        Profile the script exectuion into FILE
  --detect-product      Automatically detect the DRS product of incoming data




Some examples of usage can be found in the doctest file
``test/test_command.txt`` quoted below:

.. literalinclude:: ../test/test_command.txt
   :language: pycon


Creating esgpublish mapfiles
----------------------------

By the subcommand ``drs_tool`` mapfile will print an esgpublish
mapfile for the selected realm-tree to stdout.  For instance if you
run the test suite there will be an example drs-tree in your sandbox
called ``drs_tool_example``.  You can generate a mapfile for the atmos
domain as follows:

.. code-block:: bash

  $ drs_tool mapfile --root=drs_tool_example --product=output --institute=TEST --model=\* --realm=atmos
  drs_tool_example/output/TEST/HadCM3/1pctto4x/day/atmos/v2/rsus/r1i1p1/rsus_day_HadCM3_1pctto4x_r1i1p1_2001123114-2004010104.nc | cmip5.output.MOHC.HadCM3.1pctto4x.day.atmos
  drs_tool_example/output/TEST/HadCM3/1pctto4x/day/atmos/v2/rsus/r1i1p1/rsus_day_HadCM3_1pctto4x_r1i1p1_2004010104-2005123119.nc | cmip5.output.MOHC.HadCM3.1pctto4x.day.atmos
  drs_tool_example/output/TEST/HadCM3/1pctto4x/day/atmos/v2/rsus/r1i1p1/rsus_day_HadCM3_1pctto4x_r1i1p1_2005123119-2008010109.nc | cmip5.output.MOHC.HadCM3.1pctto4x.day.atmos
  drs_tool_example/output/TEST/HadCM3/1pctto4x/day/atmos/v2/rsus/r1i1p1/rsus_day_HadCM3_1pctto4x_r1i1p1_2000010100-2001123114.nc | cmip5.output.MOHC.HadCM3.1pctto4x.day.atmos
  ...
