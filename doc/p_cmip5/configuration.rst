Input configuration file
========================

A configuration file is required by the p_cmip5 module (which assigns the data to DRS product=output1 or output2) for processing piControl data,
and may optionally contain additional information which will ensure consistency of of the assigment for some other datasets (details below).

Example
-------

.. code-block:: ini

  [HADCM3]
  
  category=centennial
  year_piControl_spawn_to_historical=1850
  year_historical_start=1850
  year_piControl_spawn_to_abrupt4xco2=700
  year_start_abrupt4xco2=2050
  year_piControl spawn_to_1pctCo2=600
  year_start_1pctCo2=1950
  
  [HIGEM1.2]
  
  category=decadal
  year_piControl_spawn_to_historical=1850
  year_historical_start=1850
  year_piControl_spawn_to_abrupt4xco2=700
  year_start_abrupt4xco2=2050
  year_piControl spawn_to_1pctCo2=600
  year_start_1pctCo2=1950


Sections and Options
--------------------

The configuration file should contain one section for each model, containing values for:

1. category 

  :Value: either 'centennial' or 'decadal' 
  
  The category specifies which suite of experiments the model is being
  used for.  This information is use to determine what data should be
  prioritised for quality control and DOI assignment.  The aim is to
  ensure consistency between experiments and between modelling groups.

2. year_piControl_spawn_to_historical

  :Value: integer
  
  The year of the piControl data used to initiate the historical run

3. year_historical_start

  :Value: integer
  
  The year of the start of the historical run

4. year_piControl_spawn_to_abrupt4xco2

  :Value: integer
  
  The year of the piControl data used to initiate the abrupt4xco2 run

5. year_start_abrupt4xco2=2050

  :Value: integer
  
  The year of start of the abrupt4xco2 run

6. year_piControl spawn_to_1pctCo2

  :Value: integer
  
  The year of the piControl data used to initiate the 1pctCo2 run

7. year_start_1pctCo2

  :Value: integer
  
  The year of start of the 1pctCo2 run

  The first 3 are required [catgory,
  year_piControl_spawn_to_historical, year_historical_start] for
  processing piControl data in MIP tables aero, day, 6hrPlev and 3hr.
  The others are optional but may improve the consistency of data
  prioritised for replication.

