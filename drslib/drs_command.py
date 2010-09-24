"""
Command-line access to drslib

"""

import sys, os

from optparse import OptionParser

from drslib.drs_tree import DRSTree
from drslib import config
from drslib.drs import DRS

import logging
log = logging.getLogger(__name__)

usage = """usage: %prog [command] [options] [drs-pattern]

command:
  list            list publication-level datasets
  todo            show file operations pending for the next version
  upgrade         make changes to the selected datasets to upgrade to the next version.
  mapfile         make a mapfile of the selected dataset

drs-pattern:
  A dataset identifier in '.'-separated notation using '%' for wildcards
"""


def make_parser():
    op = OptionParser(usage=usage)

    op.add_option('-R', '--root', action='store',
                  help='Root directory of the DRS tree')
    op.add_option('-I', '--incoming', action='store',
                  help='Incoming directory for DRS files.  Defaults to <root>/%s' % config.DEFAULT_INCOMING)
    for attr in ['activity', 'product', 'institute', 'model', 'experiment', 
                 'frequency', 'realm']:
        op.add_option('-%s'%attr[0], '--%s'% attr, action='store',
                      help='Set DRS attribute %s for dataset discovery'%attr)

    op.add_option('-v', '--version', action='store',
                  help='Force version upgrades to this version')

    op.add_option('-P', '--profile', action='store',
                  metavar='FILE',
                  help='Profile the script exectuion into FILE')

    op.add_option('--detect-product', action='store_true',
                  help='Automatically detect the DRS product of incoming data')


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
            incoming = os.path.join(drs_root, config.DEFAULT_INCOMING)


    dt = DRSTree(drs_root)
    kwargs = {}
    for attr in ['activity', 'product', 'institute', 'model', 'experiment', 
                 'frequency', 'realm']:
        try:
            val = getattr(opts, attr)
        except AttributeError:
            val = config.drs_defaults.get(attr)
        kwargs[attr] = val

    # Get the template DRS from args
    if args:
        dataset_id = args.pop(0)
        drs = DRS.from_dataset_id(dataset_id, **kwargs)
    else:
        drs = DRS(**kwargs)

    # Product detection to be enabled later
    if opts.detect_product:
        raise NotImplementedError("Product detection is not yet implemented")

    dt.discover(incoming, **drs)
    
    return dt
    

def do_list(drs_tree, opts, args):
    print """\
==============================================================================
DRS Tree at %s
------------------------------------------------------------------------------\
""" % drs_tree.drs_root
    
    to_update = 0
    for k in sorted(drs_tree.pub_trees):
        pt = drs_tree.pub_trees[k]
        if pt.state == pt.STATE_VERSIONED:
            state_msg = '-'
        else:
            state_msg = '*'
            to_update += 1
        #!TODO: print update summary
        print '%-70s  %s' % (pt.version_drs().to_dataset_id(with_version=True), state_msg)
    
    print """\
==============================================================================\
"""

def do_todo(drs_tree, opts, args):
    for k in sorted(drs_tree.pub_trees):
        pt = drs_tree.pub_trees[k]
        if opts.version:
            next_version = int(opts.version)
        else:
            next_version = pt._next_version()

        todos = pt.list_todo(next_version)
        print """\
==============================================================================
Publisher Tree %s todo for version %d
------------------------------------------------------------------------------
%s
==============================================================================
""" % (pt.drs.to_dataset_id(), next_version, '\n'.join(todos))

def do_upgrade(drs_tree, opts, args):
    print """\
==============================================================================\
"""
    for k in sorted(drs_tree.pub_trees):
        pt = drs_tree.pub_trees[k]
        if opts.version:
            next_version = int(opts.version)
        else:
            next_version = pt._next_version()

        if pt.state == pt.STATE_VERSIONED:
            print 'Publisher Tree %s has no pending upgrades' % pt.drs.to_dataset_id()
        else:
            print ('Upgrading %s to version %d ...' % (pt.drs.to_dataset_id(), next_version)),
            pt.do_version(next_version)
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
        log.warning("PublisherTree %s has no version %d, skipping" % (pt.drs.to_dataset_id(), version))
    else:
        #!TODO: Alternative to stdout?
        pt.version_to_mapfile(version)

def run(op, command, opts, args):
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
    
    if opts.profile:
        import cProfile
        cProfile.runctx('run(op, command, opts, args)', globals(), locals(), opts.profile)
    else:
        return run(op, command, opts, args)

if __name__ == '__main__':
    main()
