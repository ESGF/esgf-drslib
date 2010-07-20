"""
Some sanity checking code for the CMIP5 MIP tables.

"""

import sqlite3

from drslib import cmip5

table_store = cmip5.get_table_store()


db = sqlite3.connect(':memory:')
c = db.cursor()

c.execute('''
create table var (
  name vchar(16),
  mip_table vchar(16),
  realm vchar(16)
)
''')
    
for table in table_store.tables.values():
    for var in table.variables:
        try:
            realms = table.get_variable_attr(var, 'modeling_realm')
        except AttributeError:
            continue
        # Only one realm should be defined but just in case
        for realm in realms:
            c.execute('insert into var values (?, ?, ?)', (var, table.name, realm))

