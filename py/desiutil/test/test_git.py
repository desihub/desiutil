# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""test desiutil.git
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
from ..git import version


class TestSetup(unittest.TestCase):
    """Test desiutil.git.
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_version(self):
        """Test automated determination of git version.
        """
        v = version('/no/such/executable')
        self.assertEqual(v, '0.0.1.dev0')
        v = version('false')
        self.assertEqual(v, '0.0.1.dev0')
        v = version('echo')
        self.assertEqual(v, 'describe .devrev-list --count HEAD')
