#!/usr/bin/env python
# BSD Licence
# Copyright (c) 2011, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os
import re

"""
Finds symlinks recursively under a given top directory, and replaces any symlinks
found pointing to absolute paths with ones pointing to relative links.

Optionally a regular expression can be supplied to 
"""

class LinkFixer:

    def __init__(self, justTesting = False):
        self.justTesting = justTesting
        self._repeatSlashesSub = re.compile("//+").sub


    def noRepeatSlashes(self, path):
        """
        get path with any repeated slashes replaced by single /
        """
        return self._repeatSlashesSub("/", path)
  
  
    def getRelTarget(self, link, target):
        """
        get relative link target given existing link path and absolute target
        """
        link = self.noRepeatSlashes(link)
        target = self.noRepeatSlashes(target)

        commonPrefix = os.path.commonprefix([link, target])
        lenCommonPrefix = len(commonPrefix)
        linkWithoutCommonPrefix = link[lenCommonPrefix :]
        targetWithoutCommonPrefix = target[lenCommonPrefix :]

        # answer is then the remaining part of the target,
        # prepended by a "../" for every slash in the remaining part of the link
        answer = ""
        for char in linkWithoutCommonPrefix:
            if char == "/":
                answer += "../"
        answer += targetWithoutCommonPrefix
                
        return answer


    def fixLink(self, link, target):
        """
        Replace an absolute link with a relative link.
        """
        newTarget = self.getRelTarget(link, target)

        print "link:", link
        print "  current target:", target
        print "  new target:", newTarget

        if not self.justTesting:
            assert(os.path.islink(link))  # sanity check
            os.remove(link)
            os.symlink(newTarget, link)
            print "done"
        print


    def findAndFixLinks(self,
                        startingDirectory,
                        callback = None, 
                        regexp = None):
        """
        Call fixLink or other callback function on every absolute symlink found 
        under starting directory, matching regexp if supplied.
        Callback should take args: link path, link target
        """
        if not startingDirectory.startswith("/"):
            raise ValueError("starting directory should be an absolute path")

        if callback == None:
            callback = self.fixLink
        if regexp != None:
            tester = re.compile(regexp).search
        else:
            tester = None
        self._findAndFixLinks(startingDirectory, callback, tester)


    def _findAndFixLinks(self,
                         startingDirectory,
                         callback,
                         tester = None):

        for fileName in os.listdir(startingDirectory):
            path = os.path.join(startingDirectory, fileName)
            if os.path.islink(path):
                if (tester == None) or tester(fileName):
                    target = os.readlink(path)
                    if target.startswith("/"):
                        callback(path, target)
            else:
                if os.path.isdir(path):
                    self._findAndFixLinks(path, callback, tester)


if __name__ == '__main__':

    fixer = LinkFixer(justTesting = False)

    fixer.findAndFixLinks('/badc/cmip5/data/cmip5/output1/MOHC',
                          regexp = "\.nc$")
