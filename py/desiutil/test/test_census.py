# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.census.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest


class TestCensus(unittest.TestCase):
    """Test desiutil.census.
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_get_options(self):
        """Test command-line argument parsing.
        """
        from ..census import get_options
        options = get_options([])
        self.assertFalse(options.verbose)
        options = get_options(['--verbose'])
        self.assertTrue(options.verbose)
        options = get_options(['-c', 'foo.yaml'])
        self.assertEqual(options.config, 'foo.yaml')

    def test_year(self):
        """Test conversion of mtime to year.
        """
        from ..census import year
        from time import gmtime
        mtime = 1475692367.0
        self.assertEqual(year(mtime), 2017)
        self.assertEqual(year(mtime, fy=False), 2016)


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
