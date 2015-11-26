# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.setup.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
import numpy as np
from ..funcfits import func_fit, func_val, iter_fit


class TestFuncFits(unittest.TestCase):
    """Test desiutil.funcfits
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_poly_fit(self):
        """Test polynomial fit
        """
        x = np.linspace(0,np.pi,50)
        y = np.sin(x)
        # Fit
        dfit = func_fit(x, y, 'polynomial', 3)
        x2 = np.linspace(0,np.pi,100)
        y2 = func_val(x2,dfit)
        np.testing.assert_allclose(y2[50], 0.97854984428713754)

    def test_legendre_fit(self):
        """Test Legendre fit
        """
        # Generate data
        x = np.linspace(0,np.pi,50)
        y = np.sin(x)
        # Fit
        dfit = func_fit(x, y, 'legendre', 4)
        x2 = np.linspace(0,np.pi,100)
        y2 = func_val(x2,dfit)
        np.testing.assert_allclose(y2[50], 0.99940823486206976)

    def test_iterfit(self):
        """Test iter fit
        """
        # Generate data
        x = np.linspace(0,np.pi,100)
        y = np.sin(x)
        #
        y[50] = 3.
        # Fit
        dfit, mask = iter_fit(x, y, 'legendre', 4)
        assert np.sum(mask) == 1
        x2 = np.linspace(0,np.pi,100)
        y2 = func_val(x2,dfit)
        np.testing.assert_allclose(y2[50], 0.99941444872371643)
