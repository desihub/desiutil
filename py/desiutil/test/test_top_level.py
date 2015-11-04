# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""test top-level desiutil functions
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
#
import unittest
import re
import sys
from .. import __version__ as theVersion
#
class TestTopLevel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.versionre = re.compile(r'([0-9]+!)?([0-9]+)(\.[0-9]+)*((a|b|rc|\.post|\.dev)[0-9]+)?')
        if sys.version_info.major == 3:
            self.assertRegexpMatches = super().assertRegexp

    def tearDown(self):
        pass

    def test_version(self):
        """Ensure the version conforms to PEP386/PEP440.
        """
        self.assertRegexpMatches(theVersion,self.versionre)

if __name__ == '__main__':
    unittest.main()
