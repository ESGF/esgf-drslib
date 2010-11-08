The configuration file.
=======================

A configuration file is required by the p_cmip5 module (which assigns the data to DRS product=output1 or output2) for processing piControl data,
and may optionally contain additional information which will ensure consistency of of the assigment for some other datasets (details below).
The configuration file should contain one section for each model, containing values for:

1. category 
-----------
Value: either 'centennial' or 'other' 

The category specifies which suite of experiments the model is being used for.
This information is use to determine what data should be prioritised for quality control and DOI assignment.
The aim is to ensure consistency between experiments and between modelling groups.
If a model is used both for centennial and decadal experiments, specify 'centennial'.

2. branch_year_piControl_to_historical
--------------------------------------
Value: integer

The year of the piControl data used to initiate the historical run.

Required if piControl data for tables aero, day or 6hrPlev is archived. This information can be determined from
the global attribute "branch" in the historical data files and the base year from the time units of the piControl
experiment. 

3. base_year_historical
-----------------------
Value: integer

The year of the start of the historical run. This is required becuase it is needed when processing piControl
data, and thus cannot generally be obtained from the data files being processed.

4. branch_year_esmControl_to_esmHistorical
------------------------------------------
Value: integer

The year of the piControl data used to initiate the historical run. See notes on 2. branch_year_piControl_to_historical

5. base_year_esmHistorical
--------------------------
Value: integer

Start of esmHistorical expt. See notes on 3. base_year_historical

6. base_year_abrupt4xCO2 [optional]
-----------------------------------
Value: integer

The year of start of the abrupt4xCO2 run. Used for processing abrupt4xCO2 data -- only needed if the base year specified
by the time units does not correspond to start of experiment.


7. base_year_piControl [optional]
---------------------------------
Value: integer

The year of start of the piControl run. Only needed if the base year specified 
by the time units does not correspond to start of experiment.

Used in determining which years of data from the aero table, piControl experiment in the decadal
suite are replicated.

8. base_year_1pctCO2 [optional]
-------------------------------
Value: integer

The year of start of the 1pctCO2 run. Only needed if the base year specified
by the time units does not correspond to start of experiment.


