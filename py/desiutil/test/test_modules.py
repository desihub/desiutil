# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""test desiutil.modules
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
#
import os
import unittest
from ..modules import init_modules
#
#
#
class TestModules(unittest.TestCase):
    """Test desiutil.modules.
    """
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @unittest.skipUnless('MODULESHOME' in os.environ,'Skipping because MODULESHOME is not defined.')
    def test_init_modules(self):
        """Test the initialization of the Modules environment.
        """
        wrapper_function = init_modules('/fake/modules/directory')
        self.assertIsNone(wrapper_function)
        wrapper_function = init_modules()
        self.assertTrue(callable(wrapper_function))
        wrapper_function = init_modules(method=True)
        self.assertTrue(callable(wrapper_function))
