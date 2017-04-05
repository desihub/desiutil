# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.plots.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
import shutil, tempfile
import os
import numpy as np
# Set non-interactive backend for Travis
try:
    import matplotlib
    matplotlib.use('agg')
    import matplotlib.pyplot as plt
    have_matplotlib = True
except ImportError:
    have_matplotlib = False

try:
    import healpy
    have_healpy = True
except ImportError:
    have_healpy = False

try:
    import mpl_toolkits.basemap
    have_basemap = True
except ImportError:
    have_basemap = False

class TestPlots(unittest.TestCase):
    """Test desiutil.plots
    """

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.plot_file = os.path.join(cls.test_dir, 'test_slices.png')
        cls.plot_file2 = os.path.join(cls.test_dir, 'test_sky.png')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    def test_masked_array_limits(self):
        """Test MaskedArrayWithLimits
        """
        from ..plots import MaskedArrayWithLimits
        data = np.arange(5.)
        mask = data < 3
        ma = MaskedArrayWithLimits(data, mask, vmin=1.0, vmax=4.0)
        self.assertEqual(ma.vmin, 1.0)
        self.assertEqual(ma.vmax, 4.0)
        ma2 = ma[0:3]
        self.assertEqual(ma2.vmin, 1.0)
        self.assertEqual(ma2.vmax, 4.0)

    def test_prepare_data(self):
        """Test prepare_data
        """
        from numpy.ma import MaskedArray
        from ..plots import prepare_data
        data = np.arange(5.)
        mask = np.array([True, False])
        with self.assertRaises(ValueError):
            ma = prepare_data(data, mask)
        mask = data == 2
        datama = MaskedArray(data, mask)
        ma = prepare_data(datama)
        self.assertIs(ma, datama)
        ma = prepare_data(data)
        self.assertTrue(np.allclose(data, ma.data))
        self.assertFalse(ma.mask.any())
        ma = prepare_data(data, mask)
        self.assertTrue(np.allclose(data, ma.data))
        self.assertTrue((ma.mask == np.array([False, False, True, False, False])).all())
        data2 = data.copy()
        data2[0] = 0.25
        data3 = data.copy()
        data3[0] = 0.25
        data3[1:] = 0.75
        data4 = data.copy()
        data4[0] = 0.75
        data4[-1] = 3.25
        ma = prepare_data(data, mask, clip_lo=0.25)
        self.assertTrue(np.allclose(data2, ma.data))
        self.assertTrue((ma.mask == np.array([False, False, True, False, False])).all())
        ma = prepare_data(data, mask, clip_lo=0.25, clip_hi=0.75)
        self.assertTrue(np.allclose(data3, ma.data))
        self.assertTrue((ma.mask == np.array([False, False, True, False, False])).all())
        ma = prepare_data(data, mask, clip_lo='25%', clip_hi='75%')
        self.assertTrue(np.allclose(data4, ma.data))
        self.assertTrue((ma.mask == np.array([False, False, True, False, False])).all())
        ma = prepare_data(data, mask, clip_lo='!25%', clip_hi='!75%')
        self.assertTrue(np.allclose(data4, ma.data))
        self.assertTrue((ma.mask == np.array([True, False, True, False, True])).all())
        ma = prepare_data(data, mask, clip_lo='25%', clip_hi='75%', save_limits=True)
        self.assertTrue(np.allclose(data4, ma.data))
        self.assertTrue((ma.mask == np.array([False, False, True, False, False])).all())
        self.assertEqual(ma.vmin, 0.75)
        self.assertEqual(ma.vmax, 3.25)

    @unittest.skipIf(not have_matplotlib,
                     'Skipping tests that require matplotlib.')
    def test_plot_slices(self):
        """Test plot_slices
        """
        # Random data
        from ..plots import plot_slices
        x = np.random.rand(1000)
        y = np.random.randn(1000)
        # Run
        ax_slices = plot_slices(x, y, 0., 1., 0.)
        ax_slices.set_ylabel('N sigma')
        ax_slices.set_xlabel('x')
        if 'TRAVIS_JOB_ID' not in os.environ:
            plt.savefig(self.plot_file)

    @unittest.skipIf(not (have_matplotlib and have_basemap),
                     'Skipping tests that require matplotlib and basemap.')
    def test_init_sky(self):
        """Test init_sky
        """
        from ..plots import init_sky

    @unittest.skipIf(not (have_matplotlib and have_basemap),
                     'Skipping tests that require matplotlib and basemap.')
    def test_plot_grid_map(self):
        from ..plots import plot_grid_map

    @unittest.skipIf(not (have_matplotlib and have_basemap),
                     'Skipping tests that require matplotlib and basemap.')
    def test_plot_sky_binned(self):
        """Test plot_sky_binned
        """
        from ..plots import plot_sky_binned

    @unittest.skipIf(not (have_matplotlib and have_basemap),
                     'Skipping tests that require matplotlib and basemap.')
    def test_plot_sky_circles(self):
        """Test plot_sky_circles
        """
        from ..plots import plot_sky_circles

    @unittest.skipIf(not (have_matplotlib and have_healpy and have_basemap),
                     'Skipping tests that require matplotlib, healpy and basemap.')
    def test_plot_sky_binned(self):
        """Test plot_sky_binned
        """
        from ..plots import plot_sky_binned
        ra = 360.*np.random.rand(200)
        dec = 360.*np.random.rand(200)
        # Run
        ax = plot_sky_binned(ra, dec)
        if 'TRAVIS_JOB_ID' not in os.environ:
            plt.savefig(self.plot_file2)


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
