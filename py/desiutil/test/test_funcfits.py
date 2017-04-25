# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.funcfits.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
import numpy as np
from warnings import catch_warnings, simplefilter
from ..funcfits import func_fit, func_val, iter_fit, mk_fit_dict


class TestFuncFits(unittest.TestCase):
    """Test desiutil.funcfits
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_mk_fit_dict(self):
        """Test fit dict
        """
        fdict = mk_fit_dict(np.arange(10), 5, 'legendre', xmin=0., xmax=5000.)
        assert isinstance(fdict,dict)

    def test_poly_fit(self):
        """Test polynomial fit.
        """
        x = np.linspace(0, np.pi, 50)
        y = np.sin(x)
        # Fit
        dfit = func_fit(x, y, 'polynomial', 3)
        x2 = np.linspace(0, np.pi, 100)
        y2 = func_val(x2, dfit)
        np.testing.assert_allclose(y2[50], 0.97854984428713754)

    def test_legendre_fit(self):
        """Test Legendre fit.
        """
        # Generate data
        x = np.linspace(0, np.pi, 50)
        y = np.sin(x)
        # Fit
        dfit = func_fit(x, y, 'legendre', 4)
        x2 = np.linspace(0, np.pi, 100)
        y2 = func_val(x2, dfit)
        np.testing.assert_allclose(y2[50], 0.99940823486206976)

    def test_cheby_fit(self):
        """Test Chebyshev fit.
        """
        # Generate data
        x = np.linspace(0, np.pi, 50)
        y = np.sin(x)
        # Fit
        dfit = func_fit(x, y, 'chebyshev', 4)
        x2 = np.linspace(0, np.pi, 100)
        y2 = func_val(x2, dfit)
        np.testing.assert_allclose(y2[50], 0.99940823486206942)

    def test_fit_with_sigma(self):
        """Test fit with sigma.
        """
        # Generate data
        x = np.linspace(0, np.pi, 50)
        y = np.sin(x)
        sigy = np.ones_like(y)*0.1
        sigy[::2] = 0.15
        # Fit
        dfit = func_fit(x, y, 'legendre', 4, w=1./sigy)
        x2 = np.linspace(0, np.pi, 100)
        y2 = func_val(x2, dfit)
        np.testing.assert_allclose(y2[50], 0.99941056289796115)

    def test_func_fit_other(self):
        """Test corner cases in fitting.
        """
        # Generate data
        x = np.linspace(0, np.pi, 50)
        y = np.sin(x)
        # Fit
        with self.assertRaises(ValueError):
            dfit = func_fit(x, y, 'fourier', 4)
        dfit = func_fit(x, y, 'polynomial', 3)
        dfit['func'] = 'fourier'
        x2 = np.linspace(0, np.pi, 100)
        with self.assertRaises(ValueError):
            y2 = func_val(x2, dfit)
        x = np.array([1.0])
        y = np.array([2.0])
        with catch_warnings(record=True) as w:
            # simplefilter("always")
            dfit = func_fit(x, y, 'polynomial', 1)
            self.assertEqual(len(w), 1)
            self.assertIn('conditioned', str(w[-1].message))
        self.assertEqual(dfit['xmin'], -1.0)
        self.assertEqual(dfit['xmax'], 1.0)

    def test_iterfit(self):
        """Test iter fit with Legendre.
        """
        # Generate data
        x = np.linspace(0, np.pi, 100)
        y = np.sin(x)
        #
        y[50] = 3.
        # Fit
        dfit, mask = iter_fit(x, y, 'legendre', 4)
        self.assertEqual(mask.sum(), 1)
        x2 = np.linspace(0, np.pi, 100)
        y2 = func_val(x2, dfit)
        np.testing.assert_allclose(y2[50], 0.99941444872371643)

    def test_iterfit2(self):
        """Test iter fit with some special cases.
        """
        # Generate data
        x = np.linspace(0, np.pi, 100)
        y = np.sin(x)
        #
        y[50] = 3.
        # Fit
        with catch_warnings(record=True) as w:
            # simplefilter("always")
            dfit, mask = iter_fit(x, y, 'legendre', 4, forceimask=True)
            self.assertEqual(len(w), 1)
            self.assertEqual(str(w[-1].message), "Initial mask cannot be enforced -- no initital mask supplied")
        x2 = np.linspace(0, np.pi, 100)
        y2 = func_val(x2, dfit)
        np.testing.assert_allclose(y2[50], 0.99941444872371643)


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
