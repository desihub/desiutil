# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.setup.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import os
import unittest
from ..setup import find_version_directory, get_version
from .. import __version__ as desiutil_version

class TestSetup(unittest.TestCase):
    """Test desiutil.setup.
    """

    @classmethod
    def setUpClass(cls):
        cls.setup_dir = os.path.abspath('.')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_find_version_directory(self):
        """Test the search for a _version.py file.
        """
        #
        # Create a fake package
        #
        save_py = os.path.isdir(os.path.join(self.setup_dir, 'py'))
        p = os.path.join(self.setup_dir, 'py', 'frobulate')
        os.makedirs(p)
        f = find_version_directory('frobulate')
        self.assertEqual(p, f)
        os.rmdir(p)
        if not save_py:
            os.rmdir(os.path.join(self.setup_dir, 'py'))
        p = os.path.join(self.setup_dir, 'frobulate')
        os.makedirs(p)
        f = find_version_directory('frobulate')
        self.assertEqual(p, f)
        os.rmdir(p)
        with self.assertRaises(IOError):
            f = find_version_directory('frobulate')

    def test_get_version(self):
        """Test parsing a _version.py file.
        """
        v = get_version('frobulate')
        self.assertEqual(v, 'unknown')
        v = get_version('desiutil')
        self.assertEqual(v, desiutil_version)
