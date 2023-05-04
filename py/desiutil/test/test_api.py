# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.api.
"""
import os
import sys
import shutil
import unittest
from unittest.mock import patch, call
from tempfile import mkdtemp
from argparse import Namespace
from ..api import find_modules, write_api


class TestApi(unittest.TestCase):
    """Test desiutil.api.
    """

    def setUp(self):
        self.temp_dir = mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('desiutil.api.find_version_directory')
    @patch('os.walk')
    def test_find_modules(self, mock_walk, mock_version):
        """Test finding modules in a package.
        """
        productroot = os.path.join(os.path.abspath('.'), 'py', 'desiutil')
        mock_version.return_value = productroot
        mock_walk.return_value = iter([(productroot, ['api', 'data', 'test'], ['__init__.py', '_version.py', 'stuff.py']),
                                       (os.path.join(productroot, 'api'), [], ['__init__.py', 'utils.py']),
                                       (os.path.join(productroot, 'data'), [], ['file1.txt', 'file2.yaml']),
                                       (os.path.join(productroot, 'test'), [], ['__init__.py', 'test_api.py', 'test_stuff.py'])])
        modules = find_modules('desiutil')
        self.assertListEqual(modules, ['desiutil', 'desiutil.stuff', 'desiutil.api', 'desiutil.api.utils'])

    def test_write_api(self):
        """Test writing out the API file.
        """
        api = """============
desiutil API
============

.. automodule:: desiutil
    :members:

.. automodule:: desiutil.api
    :members:

.. automodule:: desiutil.api.utils
    :members:

.. automodule:: desiutil.stuff
    :members:
"""
        api_file = os.path.join(self.temp_dir, 'api.rst')
        options = Namespace(name='desiutil', overwrite=False,
                            api=api_file)
        modules = ['desiutil', 'desiutil.api', 'desiutil.api.utils', 'desiutil.stuff']
        status = write_api(modules, options)
        self.assertEqual(status, 0)
        with open(api_file, 'r') as a:
            data = a.read()
        self.assertEqual(data, api)
        #
        # Test not overwriting.
        #
        status = write_api(modules, options)
        self.assertEqual(status, 1)
        #
        # Test with overwriting.
        #
        options = Namespace(name='desiutil', overwrite=True,
                            api=api_file)
        status = write_api(modules, options)
        self.assertEqual(status, 0)
        with open(api_file, 'r') as a:
            data = a.read()
        self.assertEqual(data, api)
