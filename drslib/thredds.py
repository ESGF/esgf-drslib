"""
Check metadata in a THREDDS catalog is consistent with the DRS.

Things to check:

1. All DRS components set as properties and validate with drslib
2. drs_id is consistent with properties
3. version is a date
4. dataset urlPath is consistent with the DRS directory structure.
5. Checksums are present and the right format (NOT 'MD5:...')
6. tracking_id is present
7. Check product assignement is right.

Currently implemented: 1-3

"""

import sys
import os
import re

from lxml import etree as ET
from drslib.drs import CmipDRS
from drslib.cmip5 import make_translator
import urlparse
from optparse import OptionParser

import logging
log = logging.getLogger(__name__)

THREDDS_NS = 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0'
XLINK_NS = 'http://www.w3.org/1999/xlink'

usage = """%prog [options] thredds ...

thredds:
  A thredds url or file path of a dataset published by esgpublish.\
"""



trans = make_translator('')
drs_prop_map = {'dataset_version': 'version',
                'project': 'activity',
                'experiment': 'experiment',
                'product': 'product',
                'model': 'model',
                'time_frequency': 'frequency',
                'realm': 'realm',
                'cmor_table': 'table',
                'ensemble': 'ensemble',
                'institute': 'institute'
                }


class InvalidThreddsException(Exception):
    """
    An exception raised to indicate failure of a ThreddsCheck
    """
    pass

class CheckNotPossible(Exception):
    """
    Raised to indicate a check doesn't have enough information to continue.

    """
    pass

class ThreddsCheck(object):
    """
    Base class of all checks, defining the interface.

    """

    def __init__(self, environ=None):
        """
        environ is a dictionary shared accross all checks allowing
        checks to share information.
        """
        self.environ = environ


    def check(self, etree):
        """
        Check the THREDDS catalogue represented by an ElementTree object.

        """
        pass



def run_checks(etree, checks, environ=None):
    """
    Run a sequence of checks on a THREDDS catalogue as an ElementTree.
    InvalidThreddsExceptions are converted to log messages.
 
    """
    if environ is None:
        environ = {}

    for CheckClass in checks:
        check = CheckClass(environ)
        try:
            check.check(etree)
        except InvalidThreddsException, e:
            log.error(e)
        except CheckNotPossible:
            log.warn('Check %s aborted' % CheckClass.__name__)
        else:
            log.info('Check %s succeeded' % CheckClass.__name__)

    return environ

class DRSIdCheck(ThreddsCheck):
    """
    Check drs_id is present and consistent with dataset_id.

    """

    def check(self, etree):
        dataset = get_dataset(etree)

        drs_id = get_property(dataset, 'drs_id')
        dataset_id = get_property(dataset, 'dataset_id')

        # Check 2 ids are consistent
        if drs_id != dataset_id:
            raise InvalidThreddsException("dataset_id != drs_id for dataset %s" %
                                          dataset.get('ID'))

        self.environ['dataset_id'] = dataset_id
        self.environ['drs_id'] = drs_id


class DRSPropCheck(ThreddsCheck):
    """
    Check all drs components are defined as properties.

    Creates a drs attribute in the environment if successful.

    """
    def check(self, etree):
        dataset = get_dataset(etree)

        props = {}
        for prop_name in drs_prop_map:
            prop = get_property(dataset, prop_name)
            if prop_name == 'dataset_version':
                prop = int(prop)
            elif prop_name == 'ensemble':
                #!TODO: refactor this to share code with drslib.translate
                mo = re.match(r'(?:r(\d+))?(?:i(\d+))?(?:p(\d+))?', prop)
                if not mo:
                    raise InvalidThreddsException('Unrecognised ensemble syntax %s' % prop)

                (r, i, p) = mo.groups()
                prop = tuple(x and int(x) for x in (r, i, p))

            props[drs_prop_map[prop_name]] = prop

        drs = CmipDRS(**props)

        # If present in environ check against drs_id
        if 'drs_id' in self.environ:
            if drs.to_dataset_id() != self.environ['drs_id']:
                raise InvalidThreddsException("drs properties inconsistent with drs_id for dataset %s" %
                                              dataset.get('ID'))

        self.environ['drs'] = drs


class ValidDRSCheck(ThreddsCheck):
    """
    Check the drs object in the environment is valid.

    """

    def check(self, etree):
        if 'drs' not in self.environ:
            raise CheckNotPossible

        drs = self.environ['drs']
        
        try:
            path = trans.drs_to_path(drs)
        except:
            raise InvalidThreddsException("drs %s fails to validate" % drs)


class ValidDateCheck(ThreddsCheck):
    """
    Check date versioning.

    """
    def check(self, etree):
        if not 'drs' in self.environ:
            raise CheckNotPossible

        drs = self.environ['drs']
        if not drs.version > 20100101:
            raise InvalidThreddsException("The version of dataset doesn't look like a date: %s" %
                                          drs)

#
# Utility functions
#
def get_dataset(etree):
    # There should be only 1 top-level dataset element
    datasets =  etree.findall('{%s}dataset' % THREDDS_NS)
    if len(datasets) != 1:
        raise InvalidThreddsException("More than one top-level dataset")

    return datasets[0]


def get_property(dataset, name):
    prop = dataset.find('{%s}property[@name="%s"]' % 
                      (THREDDS_NS, name))
    if prop is None:
        raise InvalidThreddsException("Property %s not found in dataset %s" % 
                                      (name, dataset.get('ID')))
                                      
    return prop.get('value')


def read_master_catalog(catalog_url):
    """
    Read master catalogue and generate dataset catalogue ElementTree objects.

    """
    cat_etree = ET.parse(catalog_url)
    scheme, netloc, path, query, fragment = urlparse.urlsplit(catalog_url)
    base_url = urlparse.urlunsplit((scheme, netloc, os.path.dirname(path)+'/', None, None))

    for catalog_ref in cat_etree.findall('{%s}catalogRef' % THREDDS_NS):
        ds_url = catalog_ref.get('{%s}href' % XLINK_NS)
        abs_ds_url = urlparse.urljoin(base_url, ds_url)
        
        yield abs_ds_url


def main(argv=sys.argv):
    logging.basicConfig(level=logging.ERROR)

    checks = [DRSIdCheck, DRSPropCheck, ValidDRSCheck, ValidDateCheck]

    op = OptionParser(usage)
    op.add_option('-c', '--catalog', action='store',
                  help="Scan root THREDDS catalog CATALOG for catalogRef "
                        "elements and check each referenced catalog")

    opts, args = op.parse_args(argv[1:])

    xmls = args
    if opts.catalog:
        log.info('Discovering catalogs from master catalog %s' % opts.catalog)
        xmls += list(read_master_catalog(opts.catalog))

    if not xmls:
        op.print_help()

    for xml in xmls:
        log.info('Checking %s' % xml)
        etree = ET.parse(xml)
        run_checks(etree, checks)

if __name__ == '__main__':
    main()
        

