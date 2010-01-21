"""
Simple parser for MIP tables

My interpretation of the format from reading the CMIP5 tables.

"""

import re

from isenes.drslib.iface import ICMORTable

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

class CMORTable(ICMORTable):
    def __init__(self, filename):
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

    def get_variable_attr(self, variable, attr):
        if variable not in self._vardict:
            raise ValueError('Variable %s not found' % variable)

        try:
            return self._vardict[variable][d]
        except KeyError:
            try:
                return self._globals[attr]
            except KeyError:
                raise AttributeError('Attribute %s not in variable or global entry' % attr)
