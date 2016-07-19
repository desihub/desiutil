# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.io.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
import sys
import numpy as np
#import pdb
from desiutil.io import yamlify, combine_dicts

try:
    basestring
except NameError:  # For Python 3
    basestring = str

class TestIO(unittest.TestCase):
    """Test desiutil.io
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_yamlify(self):
        """Test yamlify
        """
        fdict = {'name':'test', 'num':np.int32(3), 1: 'expid', 'flt32':np.float32(3.), 'flt64':np.float64(2.),
                     'num2':np.int64(4), 'bool':np.bool(True), 'lst':['tst2', np.int16(2)],
                     'tup':(1,3), 'dct':{'a':'tst3', 'b':np.float32(6.)}, 'array': np.zeros(10)}
        if sys.version_info >= (3,0,0):
            self.assertIsInstance(fdict['name'], str)
        else:
            self.assertIsInstance(fdict['name'], unicode)
        # Run
        ydict = yamlify(fdict)
        self.assertIsInstance(ydict['flt32'], float)
        self.assertIsInstance(ydict['array'], list)
        for key in ydict.keys():
            if isinstance(key, basestring):
                self.assertIsInstance(key, str)

    def test_combinedicts(self):
        """ Test combining dicts
        """
        # Merge two dicts with a common key
        dict1 = {'a': {'b':2, 'c': 3}}
        dict2 = {'a': {'d': 4}}
        dict3 = combine_dicts(dict1, dict2)
        self.assertEqual(dict3, {'a': {'b':2, 'c':3, 'd':4}})
        # Shouldn't modify originals
        self.assertEqual(dict1, {'a': {'b':2, 'c': 3}})
        self.assertEqual(dict2, {'a': {'d': 4}})
        # Merge two dicts with different keys
        dict1 = {'a': 2}
        dict2 = {'b': 4}
        dict3 = combine_dicts(dict1, dict2)
        self.assertEqual(dict3, {'a':2, 'b':4})
        self.assertEqual(dict1, {'a': 2})
        self.assertEqual(dict2, {'b': 4})
        # Overlapping leafs that are scalars should raise an error
        dict1 = {'a': 2}
        dict2 = {'a': 4}
        with self.assertRaises(ValueError):
            dict3 = combine_dicts(dict1, dict2)
        # Overlapping leafs with a scalar/dict mix raise an error
        dict1 = {'a': {'b':3}}
        dict2 = {'a': {'b':2, 'c': 3}}
        with self.assertRaises(ValueError):
            combine_dicts(dict1, dict2)
        with self.assertRaises(ValueError):
            combine_dicts(dict2, dict1)
        # Deep merge
        dict1 = {'a': {'b': {'x':1, 'y':2}}}
        dict2 = {'a': {'b': {'p':3, 'q':4}}}
        dict3 = combine_dicts(dict1, dict2)
        self.assertEqual(dict3, {'a': {'b': {'x':1, 'y':2, 'p':3, 'q':4}}})
        self.assertEqual(dict1, {'a': {'b': {'x':1, 'y':2}}})
        self.assertEqual(dict2, {'a': {'b': {'p':3, 'q':4}}})

if __name__ == '__main__':
    unittest.main()
