# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.modules.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
from os import environ, mkdir, rmdir
from os.path import dirname, join
from sys import version_info
from ..modules import init_modules, configure_module


class TestModules(unittest.TestCase):
    """Test desiutil.modules.
    """

    @classmethod
    def setUpClass(cls):
        # Data directory
        cls.data_dir = join(dirname(__file__), 't')

    @classmethod
    def tearDownClass(cls):
        pass

    @unittest.skipUnless('MODULESHOME' in environ,
                         'Skipping because MODULESHOME is not defined.')
    def test_init_modules(self):
        """Test the initialization of the Modules environment.
        """
        wrapper_function = init_modules('/fake/modules/directory')
        self.assertIsNone(wrapper_function)
        wrapper_function = init_modules()
        self.assertTrue(callable(wrapper_function))
        wrapper_function = init_modules(method=True)
        self.assertTrue(callable(wrapper_function))

    def test_configure_module(self):
        """Test detection of directories for module configuration.
        """
        test_dirs = ('bin', 'lib', 'pro', 'py')
        results = {
            'name': 'foo',
            'version': 'bar',
            'needs_bin': '',
            'needs_python': '',
            'needs_trunk_py': '# ',
            'needs_ld_lib': '',
            'needs_idl': '',
            'pyversion': "python{0:d}.{1:d}".format(*version_info)
            }
        for t in test_dirs:
            mkdir(join(self.data_dir, t))
        conf = configure_module('foo', 'bar', working_dir=self.data_dir)
        for key in results:
            self.assertEqual(conf[key], results[key])
        results['needs_python'] = '# '
        results['needs_trunk_py'] = ''
        conf = configure_module('foo', 'bar', working_dir=self.data_dir,
                                dev=True)
        for key in results:
            self.assertEqual(conf[key], results[key])
        for t in test_dirs:
            rmdir(join(self.data_dir, t))
