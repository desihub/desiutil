# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.io.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
import numpy as np
from warnings import catch_warnings, simplefilter
import pdb
from ..io import yamlify


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
        fdict = {'name':'test', 'num':np.int32(3), 'flt32':np.float32(3.), 'flt64':np.float64(2.),
                     'num2':np.int64(4), 'bool':np.bool(True), 'lst':['tst2', np.int16(2)],
                     'tup':(1,3), 'dct':{'a':'tst3', 'b':np.float32(6.)}}
        assert isinstance(fdict,dict)
        assert not isinstance(fdict['name'], str)
        assert isinstance(fdict['flt32'], np.float32)
        # Run
        ydict = yamlify(fdict)
        assert isinstance(ydict['flt32'], float)
        for key in ydict.keys():
            assert isinstance(key,str)

