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
from ..io import yamlify

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
