# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.setup.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import os
import shutil
import unittest
from ..setup import find_version_directory, get_version, update_version
from .. import __version__ as desiutil_version

class TestSetup(unittest.TestCase):
    """Test desiutil.setup.
    """

    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__), 't')
        cls.setup_dir = os.path.abspath('.')
        cls.fake_name = 'frobulate'

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.join(cls.setup_dir, cls.fake_name),
                      ignore_errors=True)

    def test_find_version_directory(self):
        """Test the search for a _version.py file.
        """
        #
        # Create a fake package
        #
        save_py = os.path.isdir(os.path.join(self.setup_dir, 'py'))
        p = os.path.join(self.setup_dir, 'py', self.fake_name)
        os.makedirs(p)
        f = find_version_directory(self.fake_name)
        self.assertEqual(p, f)
        os.rmdir(p)
        if not save_py:
            os.rmdir(os.path.join(self.setup_dir, 'py'))
        p = os.path.join(self.setup_dir, self.fake_name)
        os.makedirs(p)
        f = find_version_directory(self.fake_name)
        self.assertEqual(p, f)
        os.rmdir(p)
        with self.assertRaises(IOError):
            f = find_version_directory(self.fake_name)

    def test_get_version(self):
        """Test parsing a _version.py file.
        """
        v = get_version(self.fake_name)
        self.assertEqual(v, 'unknown')
        p = os.path.join(self.setup_dir, self.fake_name)
        os.makedirs(p)
        v = get_version(self.fake_name)
        self.assertTrue(os.path.exists(os.path.join(p, '_version.py')))
        os.remove(os.path.join(p, '_version.py'))
        os.rmdir(p)
        v = get_version('desiutil')
        self.assertEqual(v, desiutil_version)

    def test_update_version(self):
        """Test creating and updating a _version.py file.
        """
        p = os.path.join(self.setup_dir, self.fake_name)
        os.makedirs(p)
        update_version(self.fake_name)
        self.assertTrue(os.path.exists(os.path.join(p, '_version.py')))
        update_version(self.fake_name, tag='1.2.3')
        with open(os.path.join(p, '_version.py')) as f:
            data = f.read()
        self.assertEqual(data, "__version__ = '1.2.3'\n")
        os.remove(os.path.join(p, '_version.py'))
        p2 = os.path.join(self.setup_dir, self.fake_name, self.fake_name)
        os.makedirs(p2)
        original_dir = os.getcwd()
        os.chdir(p)
        with self.assertRaises(IOError):
            update_version(self.fake_name)
        os.makedirs(os.path.join(p, '.git'))
        update_version(self.fake_name)
        self.assertTrue(os.path.exists(os.path.join(p2, '_version.py')))
        os.remove(os.path.join(p2, '_version.py'))
        os.rmdir(os.path.join(p, '.git'))
        os.makedirs(os.path.join(p, '.svn'))
        update_version(self.fake_name)
        self.assertTrue(os.path.exists(os.path.join(p2, '_version.py')))
        os.remove(os.path.join(p2, '_version.py'))
        os.rmdir(os.path.join(p, '.svn'))
        os.chdir(original_dir)
        os.rmdir(p2)
        os.rmdir(p)
