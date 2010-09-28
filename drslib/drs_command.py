"""
Command-line access to drslib

"""

import sys, os, re

from optparse import OptionParser

from drslib.drs_tree import DRSTree
from drslib import config
from drslib.drs import DRS

import logging
log = logging.getLogger(__name__)

usage = """\
usage: %prog [command] [options] [drs-pattern]
       %prog --help

command:
  list            list publication-level datasets
  todo            show file operations pending for the next version
  upgrade         make changes to the selected datasets to upgrade to the next version.
  mapfile         make a mapfile of the selected dataset
  history         list all versions of the selected dataset

drs-pattern:
  A dataset identifier in '.'-separated notation using '%' for wildcards

Run %prog --help for full list of options.
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

class Command(object):
    def __init__(self, opts, args):
        self.opts = opts
        self.args = args

        self.make_drs_tree()

    def make_drs_tree(self):
        if self.opts.root:
            self.drs_root = self.opts.root
        else:
            try:
                self.drs_root = config.drs_defaults['root']
            except KeyError:
                raise Exception('drs-root not defined')

        if self.opts.incoming:
            incoming = self.opts.incoming
        else:
            try:
                incoming = config.drs_defaults['incoming']
            except KeyError:
                incoming = os.path.join(self.drs_root, config.DEFAULT_INCOMING)


        self.drs_tree = DRSTree(self.drs_root)
        kwargs = {}
        for attr in ['activity', 'product', 'institute', 'model', 'experiment', 
                     'frequency', 'realm', 'ensemble']:
            try:
                val = getattr(self.opts, attr)
            except AttributeError:
                val = config.drs_defaults.get(attr)

            kwargs[attr] = val

        # Get the template DRS from args
        if self.args:
            dataset_id = self.args.pop(0)
            drs = DRS.from_dataset_id(dataset_id, **kwargs)
        else:
            drs = DRS(**kwargs)

        # Product detection to be enabled later
        if self.opts.detect_product:
            raise NotImplementedError("Product detection is not yet implemented")
        self.drs_tree.discover(incoming, **drs)

    def do(self):
        raise NotImplementedError("Unimplemented command")
    

    def print_header(self):
        print """\
==============================================================================
DRS Tree at %s
------------------------------------------------------------------------------\
""" % self.drs_root

    def print_sep(self):
        print """\
------------------------------------------------------------------------------\
"""

    def print_footer(self):
        print """\
==============================================================================\
"""



class ListCommand(Command):
    def do(self):
        self.print_header()

        to_update = 0
        for k in sorted(self.drs_tree.pub_trees):
            pt = self.drs_tree.pub_trees[k]
            state_msg = str(pt.count_todo())
            if pt.state != pt.STATE_VERSIONED:
                to_update += 1
            #!TODO: print update summary
            print '%-70s  %s' % (pt.version_drs().to_dataset_id(with_version=True), state_msg)
    
        self.print_footer()

class TodoCommand(Command):
    def do(self):
        self.print_header()
        for k in sorted(self.drs_tree.pub_trees):
            pt = self.drs_tree.pub_trees[k]
            if self.opts.version:
                next_version = int(self.opts.version)
            else:
                next_version = pt._next_version()

            todos = pt.list_todo(next_version)
            print "Publisher Tree %s todo for version %d" % (pt.drs.to_dataset_id(),
                                                             next_version)
            self.print_sep()
            print '\n'.join(todos)
        self.print_footer()

class UpgradeCommand(Command):
    def do(self):
        self.print_header()

        for k in sorted(self.drs_tree.pub_trees):
            pt = self.drs_tree.pub_trees[k]
            if self.opts.version:
                next_version = int(self.opts.version)
            else:
                next_version = pt._next_version()

            if pt.state == pt.STATE_VERSIONED:
                print 'Publisher Tree %s has no pending upgrades' % pt.drs.to_dataset_id()
            else:
                print ('Upgrading %s to version %d ...' % (pt.drs.to_dataset_id(), next_version)),
                pt.do_version(next_version)
                print 'done'

        self.print_footer()

class MapfileCommand(Command):
    def do(self):
        """
        Generate a mapfile from the selection.  The selection must be for
        only 1 realm-tree.

        """

        if len(self.drs_tree.pub_trees) != 1:
            raise Exception("You must select 1 dataset to create a mapfile.  %d selected" %
                            len(self.drs_tree.pub_trees))

        if len(self.drs_tree.pub_trees) == 0:
            raise Exception("No datasets selected")

        pt = self.drs_tree.pub_trees.values()[0]

        #!TODO: better argument handling
        if self.args:
            version = int(self.args[0])
        else:
            version = pt.latest

        if version not in pt.versions:
            log.warning("PublisherTree %s has no version %d, skipping" % (pt.drs.to_dataset_id(), version))
        else:
            #!TODO: Alternative to stdout?
            pt.version_to_mapfile(version)

class HistoryCommand(Command):
    def do(self):
        """
        List all versions of a selected dataset.

        """
        if len(self.drs_tree.pub_trees) != 1:
            raise Exception("You must select 1 dataset to list history.  %d selected" % len(self.drs_tree.pub_trees))
        pt = self.drs_tree.pub_trees.values()[0]
        
        self.print_header()
        print "History of %s" % pt.drs.to_dataset_id()
        self.print_sep()
        for version in sorted(pt.versions, reverse=True):
            vdrs = DRS(pt.drs, version=version)
            print vdrs.to_dataset_id(with_version=True)
        self.print_footer()
            

def run(op, command, opts, args):
    if command == 'list':
        c = ListCommand(opts, args)
    elif command == 'todo':
        c = TodoCommand(opts, args)
    elif command == 'upgrade':
        c = UpgradeCommand(opts, args)
    elif command == 'mapfile':
        c = MapfileCommand(opts, args)
    elif command == 'history':
        c = HistoryCommand(opts, args)
    else:
        op.error("Unrecognised command %s" % command)

    c.do()


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
