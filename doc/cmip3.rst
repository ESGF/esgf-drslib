Translating CMIP3 to CMIP5
==========================

The script ``translate_cmip3`` converts the CMIP3 archive into a form
as close to the DRS specification as possible.  This transformation
involves both filename and directory structure changes.  From the
command's help message::
  
  Usage: translate_cmip3 [options] cmip3_root cmip5_root

  Options:
    -h, --help            show this help message and exit
    -i INCLUDE, --include=INCLUDE
                          Include paths matching INCLUDE regular expression
    -e EXCLUDE, --exclude=EXCLUDE
                          Exclude paths matching EXCLUDE regular expression
    -c, --copy            Copy rather than move files
    -d, --dryrun          Emit log messages but don't translate anything
    -l LOGLEVEL, --loglevel=LOGLEVEL
                          Set logging level


Example
-------

The drslib.cmip3 module implements a similar API to
drslib.cmip5 thus allowing CMIP3 paths to be converted to DRS
instances then converted into CMIP5 DRS format.

>>> from drslib import cmip3
>>> cmip3_trans = cmip3.make_translator('cmip3')
>>> drs3 = cmip3_trans.filepath_to_drs('cmip3/20c3m/atm/da/rsus/gfdl_cm2_0/run1/rsus_A2.19610101-19651231.nc')
>>> drs3
<DRS activity='cmip3', product='output', institute='GFDL', model='CM2', experiment='20c3m', frequency='day', realm='atmos', variable='rsus', table='A2', ensemble=(1, None, None), version=1, subset=None, extended='19610101-19651231'>
>>> cmip5_trans.drs_to_filepath(drs3)
'http://example.com/cmip5/output/GFDL/CM2/20c3m/day/atmos/v1/rsus/r1/rsus_A2_CM2_20c3m_r1_19610101-19651231.nc'

  
CMIP3 DRS components
--------------------

The CMIP3 activity is ``cmip3`` and all datasets are given the product
``output``.  The version component is always ``v1``.  Translation of
the other DRS components for CMIP3 are described below.


Institute & Model
'''''''''''''''''

Institutes and models given in capital letters and underscores are
converted to dash characters.  Capitalisation is chosen to be
consistent with the examples given in sections 3.2 and 3.3 of the DRS
specification and dashes are used to avoid ambiguity in DRS filenames
that use underscores as the component separator.

Where the exact encoding is not trivial the syntax used by the IPCC
Data Distribution Centre [DDC]_ is used.

.. [DDC] http://www.ipcc-data.org

=================   =========  =====
CMIP3 directory     Institute  Model
-----------------   ---------  -----
bcc_cm1             CMA        BCC-CM1
bccr_bcm2_0         BCCR       BCM2
cccma_cgcm3_1       CCCMA      CGCM3-1-T47
cccma_cgcm3_1_t63   CCCMA      GCM3-1-T63
cnrm_cm3            CNRM       M3
miub_echo_g         MIUB-KMA   CHO-G
csiro_mk3_0         CSIRO      K3
csiro_mk3_5  	    CSIRO      K3-5
gfdl_cm2_0  	    GFDL       M2
gfdl_cm2_1  	    GFDL       M2-1
inmcm3_0  	    INM	       M3
ipsl_cm4  	    IPSL       M4
iap_fgoals1_0_g     LASG       GOALS-G1-0
mpi_echam5  	    MPIM       CHAM5
mri_cgcm2_3_2a      MRI        GCM2-3-2
giss_aom  	    NASA       ISS-AOM
giss_model_e_h      NASA       ISS-EH
giss_model_e_r      NASA       ISS-ER
ncar_ccsm3_0  	    NCAR       CSM3
ncar_pcm1  	    NCAR       CM
miroc3_2_hires      NIES       IROC3-2-HI
miroc3_2_medres     NIES       IROC3-2-MED
ukmo_hadcm3  	    UKMO       ADCM3
ukmo_hadgem1  	    UKMO       ADGEM1
ingv_echam4  	    INGV       CHAM4
=================   =========  =====



Experiment
''''''''''

The experiment component remains unchanged from the CMIP3 archive
structure except that it's position in the tree changes to match the DRS specification.

Frequency
'''''''''

The CMIP3 frequency specifiers are translated into those described in the DRS specification as follows:

=====  ===
CMIP3  DRS
-----  ---
yr     yr
mo     mon
da     day
3h     3hr
fixed  fx
=====  ===

Modelling-realm
'''''''''''''''

We map CMIP3 realms onto equivilent CMIP5 realms.  In some cases this mapping also depends on the variable.  This mapping is defined in the table below:

===========  ========  =========
CMIP3 realm  Variable  DRS realm
-----------  --------  ---------
atm	     mrsos     land
atm	     trsult    aerosol
atm	     trsul     aerosol
atm	     tro3      atmosChem
atm	     ``*``     atmos
ice	     ``*``     seaIce
land	     sftgif    landIce
land	     ``*``     land
ocn	     ``*``     ocean
===========  ========  =========

Variable name
'''''''''''''

Variable names are left unchanged.

Ensemble member
'''''''''''''''

The encoding ``run<N>`` is translated into ``r<N>``.

Subset and extended path
''''''''''''''''''''''''

Although most filenames in the CMIP3 archive follow a consistent
syntax there are enough exceptions to make complete adherence to the
DRS specification impractical.  Instead ``translate_cmip3`` attempts to extract the variable, MIP table name from the CMIP3 path and constructs an approximate DRS filename of the form::

  <variable>_<mip-table>_<model>_<experiment>_<ensemble-member>_<extended>.nc

where ``<extended>`` is the unparsed portion of the filename that may
contain a temporal subset or may be irregular. Some examples are given below:::

  /20c3m/atm/da/rsus/gfdl_cm2_0/run1/rsus_A2.19610101-19651231.nc --> rsus_A2_CM2_20c3m_r1_19610101-19651231.nc
  /1pctto2x/atm/mo/rlftoaa_co2/ipsl_cm4/run1/rlftoaa_co2_A5_1860-1869.nc --> rlftoaa_co2_A5_CM4_1pctto2x_r1_1860-1869.nc
  /2xco2/land/fixed/orog/miroc3_2_hires/run1/orog_A1.nc --> orog_A1_MIROC3-2-HI_2xco2_r1.nc
  /sresa1b/atm/mo/rlut/cccma_cgcm3_1/run4/rlut_a1_sresa1b_4_cgcm3.1_t47_2001_2100.nc --> rlut_a1_CGCM3-1-T47_sresa1b_r4_sresa1b_4_cgcm3.1_t47_2001_2100.nc

