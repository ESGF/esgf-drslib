# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Simple parser for MIP tables.

My interpretation of the format from reading the CMIP5 tables.

"""

import re
from glob import glob
import csv

import logging
log = logging.getLogger(__name__)

entry_ids = ['axis_entry', 'variable_entry']

line_rexp = re.compile(r'(\w+):\s*(.*)')
dquote = '"(?:""|[^"])*"'
squote = "'(?:''|[^'])*'"
val_rexp = re.compile('%s|%s|!|[^!"\']+' % (dquote, squote))
expt_id_ok_rexp = re.compile('(?P<sep1>[\'"])(?P<desc>.*?)(?P=sep1)\s*(?P<sep2>[\'"])(?P<id>.*?)(?P=sep2)')

class error(Exception):
    pass

def parse_line(line):
    # Strip out comment
    line, comment = split_comment(line.strip())
    if line:
        mo = line_rexp.match(line)
        if not mo:
            raise error('Unrecognised line: %s' % line)
        entry, value = mo.groups()
        value = value.strip()
    else:
        entry = value = None

    return (entry, value, comment)


def iter_table(fh):
    """
    Generates events (entry, value, comment) by reading a MIP table from a
    file object.

    """
    for line in fh:
        line = line.strip()
        if line:
            yield parse_line(line)

def iter_entries(fh):
    """
    Generate events (entry_name, value_dict) by reading a MIP table from a
    file object.

    """
    entry_type = 'global'
    entry_name = None
    d = {}
    for name, value, comment in iter_table(fh):
        if name is None: 
            continue
        if name in entry_ids:
            yield (entry_type, entry_name, d)
            entry_type = name
            entry_name = value
            d = {}
        else:
            d.setdefault(name, []).append(value)

    yield (entry_type, entry_name, d)


def split_comment(line):
    """
    Detect comment.

    Quoted '!' characters are detected.

    """
    parts = val_rexp.findall(line)
    try:
        i = parts.index('!')
    except ValueError:
        value = ''.join(parts)
        comment = None
    else:
        value = ''.join(parts[:i])
        comment = ''.join(parts[i:])

    return (value, comment)

class MIPTable(object):
    """
    Hold information from a MIP table.  

    This information is used to enforce DRS vocabularies.

    :property name: The name of the MIP table as used in DRS filenames.
    :property variables: A list of variables in this table.
    :property experiments: A list of valid experiment ids for this table.

    """
    def __init__(self, filename):
        """
        :param filename: Name of file containing the MIP table.

        """
        fh = open(filename)
        
        self._vardict = {}

        self._read_entries(fh)
        self._init_experiments()

    def _read_entries(self, fh):
        for entry_type, entry_name, d in iter_entries(fh):
            if entry_type == 'global':
                self.name = re.match('Table (.*)', d['table_id'][0]).group(1)
                self._globals = d
            elif entry_type == 'variable_entry':
                self._vardict[entry_name] = d
            else:
                # Ignore other entry types
                pass

    def _init_experiments(self):
        self._exptdict = {}
        for value in self._globals.get('expt_id_ok', []):
            mo = expt_id_ok_rexp.match(value)
            if not mo:
                raise error("Error parsing expt_id_ok value %s" % value)
            self._exptdict[mo.group('id')] = mo.group('desc')
            

    @property
    def variables(self):
        return self._vardict.keys()

    @property
    def experiments(self):
        return self._exptdict.keys()
    
    @property
    def frequency(self):
        try:
            return self._globals['frequency'][0]
        except KeyError:
            raise AttributeError()

    def get_variable_attr(self, variable, attr):
        """
        Retrieve an attribute of variable.

        If the attributes isn't in the variable entry the global
        value is returned

        """
        if variable not in self._vardict:
            raise ValueError('Variable %s not found' % variable)

        try:
            return self._vardict[variable][attr]
        except KeyError:
            return self.get_global_attr(attr)
            
    def get_global_attr(self, attr):
        try:
            return self._globals[attr]
        except KeyError:
            raise AttributeError('Attribute %s is not a global entry' % attr)

class MIPTableStore(object):
    """
    Holds a collection of mip tables.

    :property tables: A mapping of table names to IMIPTable instances

    """

    def __init__(self, table_glob):
        """
        :param table_glob: A wildcard pattern for all MIP tables to load.

        """
        self.tables = {}

        for filename in glob(table_glob):
            self.add_table(filename)

    def add_table(self, filename):
        """
        Read filename as a MIP table and add it to the store.
        
        :return: The added MIPTable instance.

        """
        t = MIPTable(filename)
        log.info('Adding table %s from %s to table store' % (t.name, filename))
        self.tables[t.name] = t

        return t

    def get_variable_attr(self, table, variable, attr):
        """
        Return the value of a variable's attribute in a given table.

        """
        v = self.get_variable_attr_mv(table, variable, attr)
        if len(v) != 1:
            raise ValueError('%s is a multi-valued MIP attribute' % v)

        return v[0]

    def get_variable_attr_mv(self, table, variable, attr):
        """
        Return the value of a variable's attribute in a given table.

        """
        if table not in self.tables:
            raise ValueError('Table %s not found' % table)

        return self.tables[table].get_variable_attr(variable, attr)
        
    def get_global_attr(self, table, attr):
        """
        Return global table attribute.

        """
        v = self.get_global_attr_mv(table, attr)
        if len(v) != 1:
            raise ValueError('%s is a multi-valued MIP attribute' % v)

        return v[0]

    def get_global_attr_mv(self, table, attr):
        """
        Return the value of a variable's attribute in a given table.

        """
        if table not in self.tables:
            raise ValueError('Table %s not found' % table)

        return self.tables[table].get_global_attr(attr)


    #!FIXME
    #def get_variable_tables(self, variable, **attribute_constraints):
    #    ret = []
    #    for table in self.tables.values():
    #        if variable in table.variables:
    #            for k, v in attribute_constraints.items():
    #                try:
    #                    if table.get_variable_attr(variable, k) != v:
    #                        break
    #                except AttributeError:
    #                    pass
    #            else:
    #                ret.append(table.name)
    #    
    #    return ret


def read_model_table(table_csv):
    """
    Read Karl's CMIP5_models.xls file in CSV export format and 
    return a map of institute to model name.

    This function is invoked internally to load CMIP5_models.xls from inside
    drslib.

    """
    fh = open(table_csv)
    table_reader = csv.reader(fh)

    # Check first 2 lines look like the right file
    header1 = table_reader.next()
    header2 = table_reader.next()

    assert "CMIP5 Modeling Groups" in header1[0]
    assert 'Abbreviated name of center or group' in header2[1]
    assert "modified model_id" in header2[4]

    model_map = {}
    for row in table_reader:
        institute = row[1]
        model = row[4]

        # If institute contains a "/" take the first item
        if '/' in institute:
            institute = institute.split('/')[0]

        if model in model_map:
            raise "Duplicate model key %s" % model
        model_map[model] = institute

    return model_map
