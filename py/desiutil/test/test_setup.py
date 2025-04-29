# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.setup.
"""
import os
import sys
import shutil
import unittest
from unittest.mock import call, patch
from tempfile import mkdtemp
from distutils.log import INFO, WARN
from ..setup import find_version_directory, get_version, update_version
from .. import __version__ as desiutil_version


class TestSetup(unittest.TestCase):
    """Test desiutil.setup.
    """

    @classmethod
    def setUpClass(cls):
        cls.fake_name = 'frobulate'
        cls.original_dir = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        # log.set_threshold(cls.old_threshold)
        pass

    def setUp(self):
        #
        # MacOS note: os.path.abspath() is needed because /var is a
        # symlink to /private/var, but $TMPDIR just has /var.
        #
        setup_dir = mkdtemp()
        os.chdir(setup_dir)
        self.setup_dir = os.path.abspath('.')
        os.chdir(self.original_dir)

    def tearDown(self):
        os.chdir(self.original_dir)
        shutil.rmtree(self.setup_dir, ignore_errors=True)

    def test_find_version_directory(self):
        """Test the search for a _version.py file.
        """
        #
        # Create a fake package
        #
        p = os.path.join(self.setup_dir, 'py', self.fake_name)
        os.makedirs(p)
        os.chdir(self.setup_dir)
        f = find_version_directory(self.fake_name)
        self.assertEqual(p, f)
        os.rmdir(p)
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
        os.chdir(self.setup_dir)
        try:
            v = get_version(self.fake_name)
        except (OSError, IOError):
            #
            # Running in an installed package, not a git or svn checkout.
            #
            update_version(self.fake_name, tag='1.2.3')
        self.assertTrue(os.path.exists(os.path.join(p, '_version.py')))
        os.remove(os.path.join(p, '_version.py'))
        os.rmdir(p)
        os.chdir(self.original_dir)
        v = get_version('desiutil')
        self.assertEqual(v, desiutil_version)

    def test_get_version_corner_cases(self):
        """Test parsing a _version.py file with 'by-hand' formatting.
        """
        corner_cases = ("__version__ = '1.2.3'\n",  # default format
                        '__version__ = "1.2.3"\n',  # alternate quotes
                        '__version__="1.2.3"\n',  # no whitespace
                        '__version__\t=\t"1.2.3"\n',  # alternate whitespace
                        "__version__= \t\t '1.2.3'\n",  # really alternate whitespace
                        """__version__ = "1.2.3'\n""")  # mismatched quotes, should fail.
        p = os.path.join(self.setup_dir, self.fake_name)
        os.makedirs(p)
        os.chdir(self.setup_dir)
        version_file = os.path.join(p, '_version.py')
        for case in corner_cases:
            with open(version_file, 'w') as v:
                v.write(case)
            version = get_version(self.fake_name)
            if case == """__version__ = "1.2.3'\n""":
                self.assertEqual(version, 'unknown')
            else:
                self.assertEqual(version, '1.2.3')
        os.remove(os.path.join(p, '_version.py'))
        os.rmdir(p)
        os.chdir(self.original_dir)

    def test_update_version(self):
        """Test creating and updating a _version.py file.
        """
        p = os.path.join(self.setup_dir, self.fake_name)
        os.makedirs(p)
        os.chdir(self.setup_dir)
        try:
            update_version(self.fake_name)
        except (OSError, IOError):
            #
            # Running in an installed package, not a git or svn checkout.
            #
            update_version(self.fake_name, tag='0.1.2')
        self.assertTrue(os.path.exists(os.path.join(p, '_version.py')))
        update_version(self.fake_name, tag='1.2.3')
        with open(os.path.join(p, '_version.py')) as f:
            data = f.read()
        self.assertEqual(data, "__version__ = '1.2.3'\n")
        os.remove(os.path.join(p, '_version.py'))
        p2 = os.path.join(self.setup_dir, self.fake_name, self.fake_name)
        os.makedirs(p2)
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
