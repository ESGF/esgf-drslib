"""
Checker API for checking consistency of PublisherTree instances.

This API adds consistency checking to PublishTrees without bloating the PublisherTree class

"""

import os, sys
from drslib.publisher_tree import VERSIONING_LATEST_DIR

class UnfixableInconsistency(Exception):
    pass


class TreeChecker(object):
    """
    A PublisherTree is passed to TreeChecker.check() to determine if it is consistent.
    If the test result is false call repair(data) to fix.

    :cvar name: Name of the checker.  If None get_name() returns the class name.

    """

    def check(self, pt):
        """

        :param pt: PublisherTree instance to check
        :return: (result, reason, data)
        
        """
        raise NotImplementedError

    def repair(self, pt, data):
        """
        :param pt: PublisherTree instance to check
        """
        raise UnfixableInconsistency()

    def get_name(self):
        return getattr(self, 'name', self.__class__.__name__)



class CheckLatest(TreeChecker):
    def __init__(self):
        pass

    def check(self, pt):
        latest_dir = os.path.join(pt.pub_dir, VERSIONING_LATEST_DIR)
        if not os.path.exists(latest_dir):
            return (False, 'latest directory missing', None)
        
        return (True, '', None)

class CheckVersionLinks(TreeChecker):
    """
    Check all links in version directories point to real files.

    """
    def check(self, pt):
        for version in pt.versions:
            for filepath, drs in pt.versions[version]:

                realdir = pt.real_file_dir(drs.variable, drs.version)
                linkdir = pt.link_file_dir(drs.variable, drs.version)
                filename = os.path.basename(filepath)
                realpath = os.path.abspath(os.path.join(realdir, filename))
                linkpath = os.path.abspath(os.path.join(linkdir, filename))

                # filepath should be deducable from drs
                if os.path.dirname(filepath) != linkdir:
                    return (False, 'filepath %s does not match expected path %s' 
                            % (filepath, linkdir), None)


                if not os.path.exists(realpath):
                    return (False, 'realpath %s does not exist' % realpath, None)
                if not os.path.exists(linkpath):
                    return (False, 'linkpath %s does not exist' % linkpath, None)

                link = os.readlink(linkpath)
                if not os.path.isabs(link):
                    link = os.path.abspath(os.path.join(linkdir, link))

                if link != realpath:
                    return (False, 'linkpath %s does not point to %s' 
                            % (linkpath, linkpath), None)
                 
        return (True, '', None)
                

class CheckVersionFiles(TreeChecker):
    """
    Check all files in file_* are linked to a version directory.

    """

    def check(self, pt):
        fv_map = pt.file_version_map()
        versions = pt.versions.keys()

        # for each file check a link exists from that version and all subsequent versions
        #!TODO: this will need changing when file deletion is implemented

        for filename in fv_map:
            variable, fversions = fv_map[filename]

            # Add all subsequent versions
            max_fv = max(fversions)
            fversions += [v for v in versions if v > max_fv]

            for version in fversions:
                linkpath = os.path.abspath(os.path.join(pt.link_file_dir(variable, version),
                                                        filename))
                realpath = os.path.abspath(os.path.join(pt.real_file_dir(variable, version),
                                                        filename))

                # Check the files exists
                if not os.path.exists(realpath):
                    return (False, 'realpath %s does not exist' % realpath, None)
                if not os.path.exists(linkpath):
                    return (False, 'linkpath %s does not exist' % linkpath, None)

        return (True, '', None)


default_checkers = [CheckLatest(), CheckVersionLinks(), CheckVersionFiles()]
