"""
Command-line access to isenes.drslib

"""

import sys

from optparse import OptionParser

from drslib.drs_tree import DRSTree
from drslib import config

usage = """usage: %prog [command] [options]

command:
  list            list realm-trees
  todo            show file operations pending for the next version
  upgrade         make changes to the realm-tree to upgrade to the next version.
"""

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
        if rt.state == rt.STATE_INITIAL:
            status_msg = rt.state
        else:
            status_msg = '%-15s %d' % (rt.state, rt.latest)
        print '%s  %s' % (rt.realm_dir, status_msg)
    
    print """\
==============================================================================\
"""

def do_todo(drs_tree, opts, args):
    for rt in drs_tree.realm_trees:

        todos = rt.list_todo()
        print """\
==============================================================================
Realm Tree %s todo for version %d
------------------------------------------------------------------------------
%s
==============================================================================
""" % (rt.realm_dir, rt.latest+1, '\n'.join(todos))

def do_upgrade(drs_tree, opts, args):
    print """\
==============================================================================\
"""
    for rt in drs_tree.realm_trees:
        if rt.state == rt.STATE_VERSIONED:
            print 'Realm Tree %s has no pending upgrades' % rt.realm_dir
        else:
            print ('Upgrading %s to version %d ...' % (rt.realm_dir, rt.latest+1)),
            rt.do_version()
            print 'done'
    
    print """\
==============================================================================\
"""


def main(argv=sys.argv):

    op = make_parser()

    try:
        command = argv[1]
    except IndexError:
        op.error("command not specified")

    #!FIXME: better global vs. per-command help
    if command in ['-h', '--help']:
        opts, args = op.parse_args(argv[1:2])
    else:
        opts, args = op.parse_args(argv[2:])
        
    try:
        drs_tree = make_drs_tree(opts, args)

        if command == 'list':
            do_list(drs_tree, opts, args)
        elif command == 'todo':
            do_todo(drs_tree, opts, args)
        elif command == 'upgrade':
            do_upgrade(drs_tree, opts, args)
        else:
            op.error("Unrecognised command %s" % command)

    except Exception, e:
        op.error(e)
    

if __name__ == '__main__':
    main()
