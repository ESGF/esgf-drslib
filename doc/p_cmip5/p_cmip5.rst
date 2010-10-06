The p_cmip5 module will decide whether data should be assigned to DRS
product=output1 or output2. Background and the algorithm steps are
given in `requested_subset_decision_tree_v0_5.pdf`__.

__ doc/requested_subset_decision_tree_v0_5.pdf

Set-up
......

There is a set-up step performed by the code in p_cmip5/init.py, using
the "init(shelve_dir)" function.  This modules takes information from
the spreadsheets CMIP5_archive_size_template.xls and
standard_output_17Sep2010_mod.xls and stores it in python shelves used
by the main code. The shelves are placed in "shelve_dir".

The cmip5_product class
.......................

The :mod:`drslib.p_cmip5.product` module provides a ``cmip5_product`` class with a
"find_product" method. At instantiation, the class picks up
configuration tables The configuration file (sample in
ini/sample_1.ini, ini/smaple_2.ini) needs to contain information about
each model. This information is used for a small number of cases and
the format is not yet stable:

.. code-block:: python

  class cmip5_product:						 
  								 
    def __init__(self,mip_table_shelve='sh/standard_output_mip', 
                      template='sh/template',
                      stdo='sh/standard_output',
                      config='ini/sample_1.ini',
                      override_product_change_warning=False,
                      policy_opt1='all_rel',not_ok_excpt=False):   

Optional arguments
''''''''''''''''''
     :mip_table_shelve: shelve containing information about MIP tables;
     :template: shelve containing information mapping experiment names to labels used in the standard_output spreadsheet;
     :stdo: shelve containing information from the standard_output spreadsheet;
     :config: configuration file;
     :override_product_change_warning: in some cases it is possible that adding new data to previously published data can change the product
          designation of the previously published data. The default behaviour is to givw an error return at this point. This can be over-ridden, 
          the code will then provide the product of the file to be added and lists of changes that need to be made to previously published data.
          It is not expected, however, that the ESG publisher will support such updates: the user should instead compile a new set of files to
          submit using all the previously published files and the new files.
     :policy_opt1: this controls two options for treatment of data blocks in which time slices are requested. The default is that, if the time
          slices are specified using relative dates (e.g. relative to start of experiment) and the number of years submitted is les than the number
          of years requested, all years submitted will be assigned to output1 without examining the dates. There is an option (depricated) to extend
          this catch-all approach to time slices specified with absolute dates.
     :not_ok_excpt: if True, raise an exception if product can not be designated as output1 or output2.

The find_product method
.......................

The principal interface to the cmip5_product class is the find_product method:

.. code-block:: python

  def find_product(self,var,table,expt,model,path,startyear=None,endyear=None,verbose=False,
                  path_output1=None, path_output2=None,selective_ads_scan=True):

Required arguments
''''''''''''''''''
  :var: DRS variable name
  :table: MIP table
  :expt: DRS experiment name
  :model: Model name
  :path: Path to directory containing all the files of one atomic dataset.

Optional arguments
''''''''''''''''''
  :startyear: first year of the file to be assessed
  :endyear: last year of file to be assessed (not currently used)
  :verbose: if True, provide additional comments to logger
  :path_output1: path to last published output1 data for this atomic dataset, if new data is to be considered as an addition;
  :path_output2: path to last published output1 data for this atomic dataset, if new data is to be considered as an addition;
  :selective_ads_scan: when scanning the atomic dataset directory, look only at files matching the variable, table, experiment and model.
     The False option is provided to facilitate testing using dummy data files, and should not otherwise be used.
  :return: if "not_ok_excp=True", the method will return True if it can assign output1 or output2, otherwise an exception will be raised.
           if "not_ok_excpt=False", the method will return False when it cannot assign output1 or output2, with a message in pc.reason (where pc 
           is an instance of the cmip5_product class).

Attributes containing results
'''''''''''''''''''''''''''''
After successful completion of the find_product method, the followin attibutes of the instance contain information:

   :product: the product to be assigned to the file;
   :reason: a short summary of the reasons for the assigment;
   :rc: a return code, 'OKnnn' if successful, 'ERRnnn' if not.


Usage
.....

The following code fragment illustrates usage of the module::

  ## import module
  import p_cmip5_v5 as p
  
  ## create and instance of the cmip5_product class, specifying a configuration file
  ##
  pc2 = p.cmip5_product( config='ini/sample_2.ini')
  
  ## test a file: using the variable, mip table, experiment id, model and specifying the path of the atomic dataset directory containing all
  ## the submitted files.
  ## In some cases the decision as to which product the file belongs in will depend on the contents of this directory. 
  ## verbose=True results in additional messages being printed to standard out.
  
  if pc2.find_product( var, mip, expt,model,path,startyear=startyear, verbose=verbose):
    print 'product is: ', pc2.product
  
  ##  A True return means the method has identified the product
  else:
  ##  A False return means the product could not be identified
    print 'Dont know what to do with this data:: ',pc2.reason


Testing the p_cmip5 module: test_p_cmip5.py
...........................................

The test_p_cmip5 module can be used to test the p_cmip5 module. E.g. run the following from the directory containing the "test" subdirectory:

.. code-block:: bash

  $ nosetests --tests=test/test_p_cmip5.py
