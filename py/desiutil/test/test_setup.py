# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.setup.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import os
import sys
import shutil
import unittest
from distutils import log
from setuptools import sandbox
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
        cls.original_dir = os.getcwd()
        # Workaround for https://github.com/astropy/astropy-helpers/issues/124
        if hasattr(sandbox, 'hide_setuptools'):
            sandbox.hide_setuptools = lambda: None
        log.set_threshold(log.WARN)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.join(cls.setup_dir, cls.fake_name),
                      ignore_errors=True)
        shutil.rmtree(os.path.join(cls.data_dir, cls.fake_name),
                      ignore_errors=True)

    def setUp(self):
        os.chdir(self.original_dir)

    def tearDown(self):
        os.chdir(self.original_dir)

    def run_setup(self, *args, **kwargs):
        """In Python 3, on MacOS X, the import cache has to be invalidated
        otherwise new extensions built with ``run_setup`` do not always get
        picked up.
        """
        try:
            return sandbox.run_setup(*args, **kwargs)
        finally:
            if sys.version_info[:2] >= (3, 3):
                import importlib
                importlib.invalidate_caches()

    def test_version(self):
        """Test python setup.py version.
        """
        path_index = int(sys.path[0] == '')
        sys.path.insert(path_index, os.path.abspath('./py'))
        package_dir = os.path.join(self.data_dir, self.fake_name)
        os.mkdir(package_dir)
        os.mkdir(os.path.join(package_dir, self.fake_name))
        os.mkdir(os.path.join(package_dir, '.git'))
        setup = """#!/usr/bin/env python
from setuptools import setup
from desiutil.setup import DesiModule, DesiTest, DesiVersion, get_version
CMDCLASS = {{'version': DesiVersion}}
VERSION = get_version("{0.fake_name}")
setup(name="{0.fake_name}",
    version=VERSION,
    packages=["{0.fake_name}"],
    cmdclass=CMDCLASS,
    zip_safe=False)
""".format(self)
        with open(os.path.join(package_dir, 'setup.py'), 'w') as s:
            s.write(setup)
        init = """from ._version import __version__
"""
        with open(os.path.join(package_dir, self.fake_name, '__init__.py'), 'w') as i:
            i.write(init)
        os.chdir(package_dir)
        v_file = os.path.join(package_dir, self.fake_name, '_version.py')
        self.run_setup('setup.py', ['version'])
        self.assertTrue(os.path.exists(v_file))
        self.run_setup('setup.py', ['version', '--tag', '1.2.3'])
        with open(v_file) as v:
            data = v.read()
        self.assertEqual(data, "__version__ = '1.2.3'\n")
        os.chdir(self.original_dir)
        shutil.rmtree(package_dir)
        del sys.path[path_index]

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
        os.chdir(self.original_dir)
        os.rmdir(p2)
        os.rmdir(p)
