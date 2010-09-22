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
            incoming = None

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
    
    for pt in drs_tree.pub_trees.values():
        if pt.state == pt.STATE_INITIAL:
            status_msg = pt.state
        else:
            status_msg = '%-15s %d' % (pt.state, pt.latest)
        print '%s  %s' % (pt.pub_dir, status_msg)
    
    print """\
==============================================================================\
"""

def do_todo(drs_tree, opts, args):
    for pt in drs_tree.pub_trees.values():

        todos = pt.list_todo()
        print """\
==============================================================================
Publisher Tree %s todo for version %d
------------------------------------------------------------------------------
%s
==============================================================================
""" % (pt.pub_dir, pt.latest+1, '\n'.join(todos))

def do_upgrade(drs_tree, opts, args):
    print """\
==============================================================================\
"""
    for pt in drs_tree.pub_trees.values():
        if pt.state == pt.STATE_VERSIONED:
            print 'Publisher Tree %s has no pending upgrades' % pt.pub_dir
        else:
            print ('Upgrading %s to version %d ...' % (pt.pub_dir, pt.latest+1)),
            pt.do_version()
            print 'done'
    
    print """\
==============================================================================\
"""

def do_mapfile(drs_tree, opts, args):
    """
    Generate a mapfile from the selection.  The selection must be for
    only 1 realm-tree.

    """

    if len(drs_tree.pub_trees) > 1:
        raise Exception("You must select 1 realm-tree to create a mapfile.  %d selected" %
                        len(drs_tree.pub_trees))

    if len(drs_tree.pub_trees) == 0:
        raise Exception("No realm trees selected")

    pt = drs_tree.pub_trees.values()[0]

    #!TODO: better argument handling
    if args:
        version = int(args[0])
    else:
        version = pt.latest


    if version not in pt.versions:
        log.warning("PublisherTree %s has no version %d, skipping" % (pt.pub_dir, version))
    else:
        #!TODO: Alternative to stdout?
        pt.version_to_mapfile(version)

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
