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

Incoming directory
  The directory scanned for data files to be added to
  the DRS directory tree.  This directory is scanned recursively to
  find NetCDF files in the DRS filename encoding.  It defaults to
  ``<drs-root>/output`` for compatibility with the output structure of
  CMOR2.  However, the directory names under the incoming directory
  are not taken into account when deducing the DRS components of
  files.

DRS pattern
  Each invocation of ``drs_tool`` is given a set of DRS component 
  values that define the portion of the DRS space on which it acts.


Usage
-----

Usage: drs_tool [command] [options] [drs-pattern]

command:

=======  ====================================================================
list     list publication-level datasets
todo     show file operations pending for the next version
upgrade  make changes to the selected datasets to upgrade to the next version
mapfile  make a mapfile of the selected dataset
history  list all versions of the selected dataset
init     initialise CMIP5 product detection data
=======  ====================================================================

drs-pattern:
  A dataset identifier in '.'-separated notation.  Use the '%' to indicate unknown DRS components, e.g. ``cmip5.%.MPI-M`` will match any product.


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


An Example
----------

This example walks through using ``drs_tool`` to prepare datasets for
publication.  It uses some dummy data files based on test runs of the
Met Office Hadley Centre HadGEM2-ES model.  You can repeat the example
from within the drslib source distribution directory.

First generate a dummy set of incoming data files.  In this example we
assume all incoming files are in a single flat directory, however
``drs_tool`` will recursively travers the incoming directory to find
all DRS-compliant NetCDF files.

.. code-block:: bash

  $ mkdir mohc_eg
  $ python test/gen_drs.py test/mohc_delivery.ls mohc_eg/incoming
  $ ls mohc_eg/incoming/ | head
  baresoilFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_201512-204011.nc
  baresoilFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc
  baresoilFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_206512-209011.nc
  baresoilFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_209012-209911.nc
  c3PftFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_201512-204011.nc
  c3PftFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc
  c3PftFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_206512-209011.nc
  c3PftFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_209012-209911.nc
  c4PftFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_201512-204011.nc
  c4PftFrac_Lmon_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc
  $ ls mohc_eg/incoming/ | wc -l
  494

We now have about 500 dummy NetCDF files in ``mohc_eg/incoming``.  You
can ask ``drs_tool`` to list which publication-level datasets these
files would be put in using the ``drs_tool list`` subcommand.  For
this to work ``drs_tool`` requires 2 DRS components not decidable from
the filenames: activity and product [*]_.  ``drs_tool list`` will list
all publication-level datasets with the criteria given, including
those that would be created by processing the incoming directory.

.. [*] later versions of drslib will be able to decide the product
       component from other components and by inspecting the NetCDF. 

.. code-block:: bash

  $ drs_tool list -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.3hr.atmos.3hr.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.3hr.land.3hr.r1i1p1                 *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrLev.r1i1p1             *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrPlev.r1i1p1            *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.day.atmos.day.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.day.land.day.r1i1p1                 *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1             *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.atmos.Amon.r1i1p1               *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.land.Lmon.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.landIce.LImon.r1i1p1            *
  ==============================================================================

The asterisk against each dataset_id indicates there are files in the
incoming directory to add to the dataset.  In this case all datasets
are empty.

We can restrict ``drs_tool list`` output by using a dataset_id
wildcard.  For instance to select only datasets in the ``atmos`` realm:

.. code-block:: bash

  $ drs_tool list -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1.%.%.%.%.atmos
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.3hr.atmos.3hr.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrLev.r1i1p1             *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrPlev.r1i1p1            *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.day.atmos.day.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.atmos.Amon.r1i1p1               *
  ==============================================================================

The same effect can be achieved with individual component options:

.. code-block:: bash

  $ drs_tool list -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1 --realm=atmos
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.3hr.atmos.3hr.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrLev.r1i1p1             *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrPlev.r1i1p1            *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.day.atmos.day.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.atmos.Amon.r1i1p1               *
  ==============================================================================

Now we will focus on a single dataset in the ``aerosol`` realm and
show how to move files into the DRS directory structure ready for
publication.  We can check what filesystem commands will be done using
the ``drs_tool todo`` subcommand.

.. code-block:: bash

  $ drs_tool list -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1 --realm=aerosol
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1             *
  ==============================================================================
  $ drs_tool todo -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1 --realm=aerosol | head
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  Publisher Tree cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1 todo for version 20100927
  ------------------------------------------------------------------------------
  mv mohc_eg/incoming/emidust_aero_HadGEM2-ES_rcp45_r1i1p1_206512-209011.nc /home/spascoe/git/esgf-drslib/mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/files/emidust_20100927/emidust_aero_HadGEM2-ES_rcp45_r1i1p1_206512-209011.nc
  ln -s /home/spascoe/git/esgf-drslib/mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/files/emidust_20100927/emidust_aero_HadGEM2-ES_rcp45_r1i1p1_206512-209011.nc /home/spascoe/git/esgf-drslib/mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/emidust/emidust_aero_HadGEM2-ES_rcp45_r1i1p1_206512-209011.nc
  mv mohc_eg/incoming/reffclwtop_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc /home/spascoe/git/esgf-drslib/mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/files/reffclwtop_20100927/reffclwtop_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc
  ln -s /home/spascoe/git/esgf-drslib/mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/files/reffclwtop_20100927/reffclwtop_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc /home/spascoe/git/esgf-drslib/mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/reffclwtop/reffclwtop_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc
  mv mohc_eg/incoming/dryso2_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc /home/spascoe/git/esgf-drslib/mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/files/dryso2_20100927/dryso2_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc

You can see here that drslib will move files into datestamped
directories under ``<dataset-dir>/files`` then symbolically link them
into the DRS directory structure.  To do the actual moving use
``drs_tool upgrade``.  Then use ``drs_tool list`` to view the result.

.. code-block:: bash

  $ drs_tool upgrade -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1 --realm=aerosol
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  Upgrading cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1 to version 20100927 ... done
  ==============================================================================
  $ drs_tool list -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.3hr.atmos.3hr.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.3hr.land.3hr.r1i1p1                 *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrLev.r1i1p1             *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrPlev.r1i1p1            *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.day.atmos.day.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.day.land.day.r1i1p1                 *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1.v20100927   -
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.atmos.Amon.r1i1p1               *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.land.Lmon.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.landIce.LImon.r1i1p1            *
  ==============================================================================

Using ``drs_tool``'s criteria options you can upgrade multiple datasets in one command:

.. code-block:: bash

  $ drs_tool upgrade -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1 --realm=atmos --frequency=6hr
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  Upgrading cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrLev.r1i1p1 to version 20100927 ... done
  Upgrading cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrPlev.r1i1p1 to version 20100927 ... done
  ==============================================================================
  $ drs_tool list -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1
  ==============================================================================
  DRS Tree at mohc_eg/
  ------------------------------------------------------------------------------
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.3hr.atmos.3hr.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.3hr.land.3hr.r1i1p1                 *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrLev.r1i1p1.v20100927   -
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.6hr.atmos.6hrPlev.r1i1p1.v20100927  -
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.day.atmos.day.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.day.land.day.r1i1p1                 *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1.v20100927   -
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.atmos.Amon.r1i1p1               *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.land.Lmon.r1i1p1                *
  cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.landIce.LImon.r1i1p1            *
  ==============================================================================

Finally you need to send publish the datasets with ``esgpublish``.  To make this easier ``drs_tool`` can create a mapfile of a dataset:

.. code-block:: bash

  $ drs_tool mapfile -R mohc_eg/ -I mohc_eg/incoming/ cmip5.output1 --realm=aerosol >rcp45.mon.aerosol.map
  $ head rcp45.mon.aerosol.map 
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/loadsoa/loadsoa_aero_HadGEM2-ES_rcp45_r1i1p1_206512-209011.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/loadsoa/loadsoa_aero_HadGEM2-ES_rcp45_r1i1p1_209012-209911.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/loadsoa/loadsoa_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/loadsoa/loadsoa_aero_HadGEM2-ES_rcp45_r1i1p1_201512-204011.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/loadbc/loadbc_aero_HadGEM2-ES_rcp45_r1i1p1_201512-204011.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/loadbc/loadbc_aero_HadGEM2-ES_rcp45_r1i1p1_206512-209011.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/loadbc/loadbc_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/loadbc/loadbc_aero_HadGEM2-ES_rcp45_r1i1p1_209012-209911.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/wetbc/wetbc_aero_HadGEM2-ES_rcp45_r1i1p1_209012-209911.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1
  mohc_eg/output1/MOHC/HadGEM2-ES/rcp45/mon/aerosol/aero/r1i1p1/v20100927/wetbc/wetbc_aero_HadGEM2-ES_rcp45_r1i1p1_204012-206511.nc | cmip5.output1.MOHC.HadGEM2-ES.rcp45.mon.aerosol.aero.r1i1p1



Some further examples of usage can be found in the doctest file
``test/test_command.txt``.
