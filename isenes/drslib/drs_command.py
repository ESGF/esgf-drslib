"""
Command-line access to isenes.drslib

"""

import sys

from optparse import OptionParser

from isenes.drslib.drs_tree import DRSTree
from isenes.drslib import config

usage = """usage: %prog [command] [options]

command:
  list            list realm-trees"""

def make_parser():
    op = OptionParser(usage=usage)

    op.add_option('-R', '--root', action='store',
                  help='Root directory of the DRS tree')
    for attr in ['product', 'institute', 'model', 'experiment', 
                 'frequency', 'realm']:
        op.add_option('-%s'%attr[0], '--%s'% attr, action='store',
                      help='Set DRS attribute %s for realm-tree discovery'%attr)

    return op

def make_drs_tree(opts, args):
    if opts.root:
        drs_root = opts.root
    else:
        try:
            drs_root = config.drs_defaults['root']
        except KeyError:
            raise Exception('drs-root not defined')

    dt = DRSTree(drs_root)
    kwargs = {}
    for attr in ['product', 'institute', 'model', 'experiment', 
                 'frequency', 'realm']:
        try:
            val = getattr(opts, attr)
        except AttributeError:
            val = config.drs_defaults.get(attr)
        kwargs[attr] = val

    dt.discover(**kwargs)
    
    return dt
    

def do_list(drs_tree, opts, args):
    print """\
==============================================================================
DRS Tree at %s
------------------------------------------------------------------------------\
""" % drs_tree.drs_root
    for rt in drs_tree.realm_trees:
        print '%s  %s' % (rt.realm_dir, rt.state)
    
    print """\
------------------------------------------------------------------------------\
"""


def main(argv=sys.argv):

    op = make_parser()

    try:
        command = argv[1]
    except IndexError:
        op.error("command not specified")

    opts, args = op.parse_args(argv[2:])
    try:
        drs_tree = make_drs_tree(opts, args)
    except Exception, e:
        op.error(e)

    if command == 'list':
        do_list(drs_tree, opts, args)

if __name__ == '__main__':
    main()
