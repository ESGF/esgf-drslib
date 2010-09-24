``drs_tree`` command-line interface
===================================

The ``drs_tool`` command can be used to invoke functions from the
:mod:`drslib.drs_tree` API.

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
