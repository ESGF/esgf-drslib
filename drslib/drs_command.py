# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Command-line access to drslib

"""

import sys, os

from optparse import OptionParser
from ConfigParser import NoSectionError, NoOptionError
import json

from drslib.drs_tree import DRSTree
from drslib import config
from drslib.drs import CmipDRS

from drslib import p_cmip5
from drslib.cmip5 import CMIP5FileSystem

import logging
from warnings import warn
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
  init            initialise CMIP5 data for product detection
  diff            list differences between versions or between a version and the todo list
  repair          Fix problems that are shown by the list command

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
    #!TODO: Warn on all these options
    for attr in ['activity', 'product', 'institute', 'model', 'experiment', 
                 'frequency', 'realm']:
        op.add_option('--%s'% attr, action='store',
                      help='DEPRECATED, use --component instead')

    def component_cb(option, opt_str, value, parser):
        component, cvalue = value.split('=')
        try:
            component_dict = parser.values.component_dict
        except AttributeError:
            component_dict = parser.values.component_dict = {}

        component_dict[component] = cvalue            

    op.add_option('-c', '--component', action='callback', 
                  callback=component_cb, type='str',
                  help='Set DRS components for dataset discovery')

    op.add_option('-v', '--version', action='store',
                  help='Force version upgrades to this version')

    op.add_option('-P', '--profile', action='store',
                  metavar='FILE',
                  help='Profile the script exectuion into FILE')

    op.add_option('-s', '--scheme', action='store',
                  help='Select the DRS scheme to use.  Available schemes are %s' % ', '.join(config.drs_schemes))

    # p_cmip5 options
    op.add_option('--detect-product', action='store_true', 
                  help='Automatically detect the DRS product of incoming data')
    op.add_option('--shelve-dir', action='store',
                  help='Location of the p_cmip5 data directory')
    op.add_option('--p-cmip5-config', action='store',
                  help='Location of model-specific configuration file for p_cmip5')

    op.add_option('-M', '--move-cmd', action='store',
                  help='Set the command used to move files into the DRS structure')

    op.add_option('-j', '--json-drs', action='store',
                  help='Obtain DRS information from the json file FILE instead of deducing it from file paths')

    return op

class Command(object):
    def __init__(self, op, opts, args):
        self.op = op
        self.opts = opts
        self.args = args
        self.shelve_dir = None
        self.p_cmip5_config = None
        self.drs_root = None
        self.drs_tree = None

        self.make_drs_tree()

    def _config_p_cmip5(self):
        """
        Ensure self.shelve_dir is set.  This is required for InitCommand
        and any command that uses p_cmip5.

        """
        self.shelve_dir = self.opts.shelve_dir
        if self.shelve_dir is None:
            try:
                self.shelve_dir = config.config.get('p_cmip5', 'shelve-dir')
            except NoSectionError:
                raise Exception("Shelve directory not specified.  Please use --shelve-dir or set shelve_dir via metaconfig")

    def _setup_p_cmip5(self):
        """
        Instantiate the p_cmip5.cmip5_product object ready for deducing
        the product component.

        """
        
        shelves = p_cmip5.init._find_shelves(self.shelve_dir)
    
        self.p_cmip5_config = self.opts.p_cmip5_config
        if self.p_cmip5_config is None:
            try:
                self.p_cmip5_config = config.config.get('p_cmip5', 'config')
            except (NoSectionError, NoOptionError):
                raise Exception("p_cmip5 configuration file not specified.  Please use --p-cmip5-config or set via metaconfig")

        self.drs_tree.set_p_cmip5(p_cmip5.product.cmip5_product(
                mip_table_shelve=shelves['stdo_mip'],
                template=shelves['template'],
                stdo=shelves['stdo'],
                config=self.p_cmip5_config,
                not_ok_excpt=True))


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

        if self.opts.json_drs:
            json_drs = self.opts.json_drs
        else:
            json_drs = None

        drs_root = os.path.normpath(os.path.abspath(self.drs_root))

        if self.opts.scheme:
            scheme = self.opts.scheme
        else:
            scheme = config.default_drs_scheme

        try:
            fs_cls = config.get_drs_scheme(scheme)
        except KeyError:
            raise ValueError('Unrecognised DRS scheme %s' % scheme)
    
        self.drs_fs = fs_cls(drs_root)
        self.drs_tree = DRSTree(self.drs_fs)

        if self.opts.move_cmd:
            self.drs_tree.set_move_cmd(self.opts.move_cmd)


        # This code is specifically for the deprecated DRS setting options
        # Generic DRS component setting is handled below
        kwargs = {}
        for attr in ['activity', 'product', 'institute', 'model', 'experiment', 
                     'frequency', 'realm', 'ensemble']:
            try:
                val = getattr(self.opts, attr)
                # val may be there but None
                if val is None:
                    raise AttributeError
                warn('Option --%s is deprecated.  Use --component instead' % attr)

            except AttributeError:
                val = config.drs_defaults.get(attr)

            # Only add this component if it is valid for the DRS scheme
            if attr in self.drs_fs.drs_cls.DRS_ATTRS:
                log.info('Setting DRS component %s=%s' % (attr, val))
                kwargs[attr] = val

        try:
            component_dict = self.opts.component_dict
        except AttributeError:
            component_dict = {}

        for component in self.drs_fs.drs_cls._iter_components(to_publish_level=True):
            if component in component_dict:
                val = component_dict.get(component)
                log.info('Setting DRS component %s=%s' % (component, val))
                kwargs[component] = val
                del component_dict[component]

        # Error for any components not valid
        for component in component_dict:
            op.error('Unrecognised component %s for scheme %s' % (component,
                                                                  scheme))


        # Get the template DRS from args
        if self.args:
            dataset_id = self.args[0]
            drs = self.drs_fs.drs_cls.from_dataset_id(dataset_id, **kwargs)
        else:
            drs = self.drs_fs.drs_cls(**kwargs)

        # Product detection
        if self.opts.detect_product:
            self._config_p_cmip5()
            self._setup_p_cmip5()

        # If JSON file selected use that, otherwise discover from filesystem
        if json_drs:
            with open(json_drs) as fh:
                #!TODO: Remove json-array case
                # This is a work-around until we have a stable json format
                # The file might be a json array or it might be a series
                # of json files, 1 per line
                json_str = fh.readline()
                if json_str[0] == '[':
                    json_obj = json.loads(json_str)
                else:
                    json_obj = []
                    while json_str:
                        json_obj.append(json.loads(json_str))
                        json_str = fh.readline()

            self.drs_tree.discover_incoming_fromjson(json_obj, **drs)
        else:
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

        to_upgrade = 0
        broken = 0
        for k in sorted(self.drs_tree.pub_trees):
            pt = self.drs_tree.pub_trees[k]
            todo = pt.count_todo()
            if todo:
                state_msg = '%d:%d %d:%d' % (pt.count(), pt.size(), todo, pt.todo_size())
            else:
                state_msg = '%d:%d' % (pt.count(), pt.size())
            if pt.state == pt.STATE_BROKEN:
                broken += 1
            elif pt.state != pt.STATE_VERSIONED:
                to_upgrade += 1
            #!TODO: print update summary
            print '%-70s  %s' % (pt.version_drs().to_dataset_id(with_version=True), state_msg)
    
        if self.drs_tree.incomplete:
            self.print_sep()
            print 'Incompletely specified incoming datasets'
            self.print_sep()
            for dataset_id in sorted(self.drs_tree.incomplete_dataset_ids()):
                print '%-70s' % dataset_id

        if to_upgrade or broken:
            self.print_sep()
            if to_upgrade:
                print '%d datasets awaiting upgrade' % to_upgrade
            if broken:
                if config.check_latest:
                    print '%d datasets have broken latest versions' % broken
                else:
                    print '%d datasets are broken' % broken

        self.print_sep()
        for pt in self.drs_tree.pub_trees.values():
            if pt.has_failures():
                print 'FAIL %-70s' % pt.drs.to_dataset_id()
                for line in pt.list_failures():
                    print '  ', line

        self.print_footer()

class TodoCommand(Command):
    def do(self):
        self.print_header()
        first = True
        for k in sorted(self.drs_tree.pub_trees):
            pt = self.drs_tree.pub_trees[k]

            if pt.count_todo() == 0:
                if not first: 
                    self.print_sep()
                print 'Nothing todo for %s' % pt.drs.to_dataset_id()
                first = False
                continue

            if self.opts.version:
                next_version = int(self.opts.version)
            else:
                next_version = pt._next_version()

            todos = pt.list_todo(next_version)
            if not first:
                self.print_sep()
            print "Publisher Tree %s todo for version %d" % (pt.drs.to_dataset_id(),
                                                             next_version)
            first = False
            print
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
                to_process = pt.count_todo()
                pt.do_version(next_version)
                print 'done %d' % to_process

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
        if len(self.args) > 1:
            version = int(self.args[1])
        else:
            version = pt.latest

        if version not in pt.versions:
            log.warning("PublisherTree %s has no version %d, skipping" % (pt.drs.to_dataset_id(), version))
        else:
            #!TODO: Alternative to stdout?
            pt.version_to_mapfile(version, checksum_func=config.checksum_func)

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
            vdrs = self.drs_fs.drs_cls(pt.drs, version=version)
            print vdrs.to_dataset_id(with_version=True)
        self.print_footer()
            

class InitCommand(Command):
    def make_drs_tree(self):
        """No need to initialise the drs tree for this command.
        """
        pass

    def do(self):
        self._config_p_cmip5()

        from drslib.p_cmip5.init import init
        init(self.shelve_dir, config.table_path)

        print "CMIP5 configuration data written to %s" % repr(self.shelve_dir)


class RepairCommand(Command):
    def do(self):
        for drs_id, pt in self.drs_tree.pub_trees.items():
            if pt.has_failures():
                print 'FIXING %-70s' % drs_id
                pt.repair()
                for line in pt.list_failures():
                    print '  ', line


class DiffCommand(Command):
    """
    Accepts 0-2 arguments.  If no arguments given lists the diff between
    the latest version and the todo list.  If 1 given lists  the diff
    between that version and the todo list.  If 2 given lists the diff
    between these versions.

    """
    def do(self):
        if len(self.drs_tree.pub_trees) != 1:
            raise Exception("You must select 1 dataset to view differences. %d selected" %
                            len(self.drs_tree.pub_trees))

        if len(self.drs_tree.pub_trees) == 0:
            raise Exception("No datasets selected")

        pt =self.drs_tree.pub_trees.values()[0]

        #!TODO: better argument handling
        args = self.args[:]
        if not args:
            v1 = pt.latest
            v2 = None
        else:
            v1 = int(args.pop(0))
            if args:
                v2 = int(args.pop(0))
            else:
                v2 = None
        
        # Yields DIFF_STATE, file1, file2

        self.print_header()
        if v2:
            v2_msg = v2
        else:
            v2_msg = 'todo list'
        print 'Diff between %s and %s' % (v1, v2_msg)
        self.print_sep()

        #!FIXME: Just compare file sizes at the moment!
        for diff_type, f1, f2 in pt.diff_version(v1, v2):
            filename = os.path.basename(f1 or f2)
            if diff_type == pt.DIFF_NONE:
                continue
            # Don't compare by path if using the todo list
            elif (v2 is not None) and (diff_type & pt.DIFF_PATH == pt.DIFF_PATH):
                print 'PATH\t\t%s' % filename
            elif diff_type & pt.DIFF_SIZE == pt.DIFF_SIZE:
                print 'SIZE\t\t%s' % filename
            elif diff_type & pt.DIFF_TRACKING_ID == pt.DIFF_TRACKING_ID:
                print 'TRACKING_ID\t%s' % filename
            elif diff_type & pt.DIFF_V1_ONLY == pt.DIFF_V1_ONLY:
                print '%s\t\t%s' % (v1, filename)
            elif diff_type & pt.DIFF_V2_ONLY == pt.DIFF_V2_ONLY:
                print '%s\t\t%s' % (v2_msg, filename)
            else:
                assert False
                
        self.print_footer()

def run(op, command, opts, args):
    commands = []

    if command == 'list':
        commands.append(ListCommand)
    elif command == 'todo':
        commands.append(TodoCommand)
    elif command == 'upgrade':
        commands.append(UpgradeCommand)
    elif command == 'mapfile':
        commands.append(MapfileCommand)
    elif command == 'history':
        commands.append(HistoryCommand)
    elif command == 'init':
        commands.append(InitCommand)
    elif command == 'diff':
        commands.append(DiffCommand)
    elif command == 'repair':
        commands.append(RepairCommand)
        commands.append(ListCommand)
    else:
        op.error("Unrecognised command %s" % command)

    for klass in commands:
        c = klass(op, opts, args)
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
