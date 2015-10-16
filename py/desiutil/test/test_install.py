# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
test util.install
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
#
import unittest
from ..install import version
#
class TestInstall(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_version(self):
        """Test version parser.
        """
        v = version("$HeadURL: https://desi.lbl.gov/svn/code/tools/desiUtil/tags/0.5.5/py/desiutil/test/test_install.py $")
        self.assertEqual(v,'0.5.5', 'Failed to extract version, got {0}.'.format(v))
        v = version("$HeadURL$")
        self.assertEqual(v,'0.0.1.dev', 'Failed to return default version, got {0}.'.format(v))

if __name__ == '__main__':
    unittest.main()
