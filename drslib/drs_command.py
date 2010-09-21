"""
Command-line access to drslib

"""

import sys

from optparse import OptionParser

from drslib.drs_tree import DRSTree
from drslib import config

import logging
log = logging.getLogger(__name__)

usage = """usage: %prog [command] [options]

command:
  list            list realm-trees
  todo            show file operations pending for the next version
  upgrade         make changes to the realm-tree to upgrade to the next version.
  mapfile         make a mapfile of the selected realm-trees
"""


def make_parser():
    op = OptionParser(usage=usage)

    op.add_option('-R', '--root', action='store',
                  help='Root directory of the DRS tree')
    op.add_option('-I', '--incoming', action='store',
                  help='Incoming directory for DRS files')
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

    if opts.incoming:
        incoming = opts.incoming
    else:
        try:
            incoming = config.drs_defaults['incoming']
        except KeyError:
            raise Exception('incoming directory not defined')

    dt = DRSTree(drs_root)
    kwargs = {}
    for attr in ['product', 'institute', 'model', 'experiment', 
                 'frequency', 'realm']:
        try:
            val = getattr(opts, attr)
        except AttributeError:
            val = config.drs_defaults.get(attr)
        kwargs[attr] = val

    dt.discover(incoming, **kwargs)
    
    return dt
    

def do_list(drs_tree, opts, args):
    print """\
==============================================================================
DRS Tree at %s
------------------------------------------------------------------------------\
""" % drs_tree.drs_root
    
    for rt in drs_tree.realm_trees.values():
        if rt.state == rt.STATE_INITIAL:
            status_msg = rt.state
        else:
            status_msg = '%-15s %d' % (rt.state, rt.latest)
        print '%s  %s' % (rt.realm_dir, status_msg)
    
    print """\
==============================================================================\
"""

def do_todo(drs_tree, opts, args):
    for rt in drs_tree.realm_trees.values():

        todos = rt.list_todo()
        print """\
==============================================================================
Publisher Tree %s todo for version %d
------------------------------------------------------------------------------
%s
==============================================================================
""" % (rt.realm_dir, rt.latest+1, '\n'.join(todos))

def do_upgrade(drs_tree, opts, args):
    print """\
==============================================================================\
"""
    for rt in drs_tree.realm_trees.values():
        if rt.state == rt.STATE_VERSIONED:
            print 'Publisher Tree %s has no pending upgrades' % rt.realm_dir
        else:
            print ('Upgrading %s to version %d ...' % (rt.realm_dir, rt.latest+1)),
            rt.do_version()
            print 'done'
    
    print """\
==============================================================================\
"""

def do_mapfile(drs_tree, opts, args):
    """
    Generate a mapfile from the selection.  The selection must be for
    only 1 realm-tree.

    """

    if len(drs_tree.realm_trees) > 1:
        raise Exception("You must select 1 realm-tree to create a mapfile.  %d selected" %
                        len(drs_tree.realm_trees))

    if len(drs_tree.realm_trees) == 0:
        raise Exception("No realm trees selected")

    rt = drs_tree.realm_trees[0]

    #!TODO: better argument handling
    if args:
        version = int(args[0])
    else:
        version = rt.latest


    if version not in rt.versions:
        log.warning("PublisherTree %s has no version %d, skipping" % (rt.realm_dir, version))
    else:
        #!TODO: Alternative to stdout?
        rt.version_to_mapfile(version)

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
        elif command == 'mapfile':
            do_mapfile(drs_tree, opts, args)
        else:
            op.error("Unrecognised command %s" % command)

    except Exception, e:
        log.exception(e)
        op.error(e)
    

if __name__ == '__main__':
    main()
