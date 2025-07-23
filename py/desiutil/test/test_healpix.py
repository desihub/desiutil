# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.healpix.
"""
import unittest
import numpy as np
from ..healpix import radec2hpix, radec2upix, hpix2upix, upix2hpix
from ..healpix import is_in_sorted_array
from ..healpix import partition_radec, find_upix


class TestHealpix(unittest.TestCase):
    """Test desiutil.healpix
    """

    def test_radec2hpix(self):
        """Test radec2hpix"""

        # vector input
        ra = np.arange(0, 361, 60)
        dec = np.arange(-90, 91, 30)
        assert len(ra) == len(dec)
        hpix64 = radec2hpix(64, ra, dec)
        hpix128 = radec2hpix(128, ra, dec)

        self.assertListEqual(
            list(hpix64),
            [32768, 33255, 39769, 26282,  9382, 15896,  4095])
        self.assertListEqual(list(hpix128//4), list(hpix64))

        # scalar input
        x = radec2hpix(64, ra[0], dec[0])
        self.assertEqual(x, hpix64[0])

    def test_radec2upix(self):
        """Test radec2upix"""

        # vector input
        ra = np.arange(0, 361, 60)
        dec = np.arange(-90, 91, 30)
        assert len(ra) == len(dec)
        hpix128 = radec2hpix(128, ra, dec)
        upix128 = hpix128 + 4*128**2
        self.assertListEqual(list(radec2upix(128, ra, dec)), list(upix128))
        self.assertListEqual(list(radec2upix(64, ra, dec)), list(upix128//4))
        self.assertListEqual(list(radec2upix(32, ra, dec)), list(upix128//16))

        # scalar input
        x = radec2upix(128, ra[1], dec[1])
        self.assertEqual(x, upix128[1])

    def test_upix_hpix(self):
        """Test upix2hpix and hpix2upix"""
        nside = np.array([16, 32, 64, 128])
        hpix = np.array([1000, 2000, 3000, 4000])

        # hpix -> upix
        upix = hpix2upix(nside, hpix)
        self.assertListEqual(list(upix), list(hpix + 4*nside**2))  # vector vector
        self.assertEqual(hpix2upix(nside[0], hpix[0]), upix[0])    # scalar scalar
        self.assertListEqual(list(hpix2upix(nside[0], hpix)), list(hpix + 4*nside[0]**2))  # scalar vector

        # upix -> hpix
        tmp_nside, tmp_hpix = upix2hpix(upix)
        self.assertListEqual(list(tmp_nside), list(nside))
        self.assertListEqual(list(tmp_hpix), list(hpix))
        self.assertEqual(upix2hpix(upix[0]), (nside[0], hpix[0]))

    def test_is_in_sorted_array(self):
        """Test is_in_sorted_array"""
        self.assertEqual(is_in_sorted_array(0, [1, 2, 5]), False)
        self.assertEqual(is_in_sorted_array(1, [1, 2, 5]), True)
        self.assertEqual(is_in_sorted_array(2, [1, 2, 5]), True)
        self.assertEqual(is_in_sorted_array(3, [1, 2, 5]), False)
        self.assertEqual(is_in_sorted_array(4, [1, 2, 5]), False)
        self.assertEqual(is_in_sorted_array(5, [1, 2, 5]), True)
        self.assertEqual(is_in_sorted_array(6, [1, 2, 5]), False)
        self.assertListEqual(list(is_in_sorted_array([10, 5, 0, 2, 3], [1, 2, 5])),
                             [False, True, False, True, False])

    def test_partition_radec(self):
        """test partition_radec and find_upix"""

        # partition points into unique pixels
        rand = np.random.RandomState(0)
        n = 1000
        nmax_per_healpix = 50
        ra = rand.normal(180, 10, n)
        dec = rand.normal(0, 10, n)
        upix = partition_radec(ra, dec, nmax_per_healpix)
        nside, hpix = upix2hpix(upix)

        # confirm that we actually got different nside hierarchy
        self.assertEqual(len(upix), n)
        self.assertGreater(len(np.unique(nside)), 1)

        # confirm that max(entries) < nmax_per_healpix
        available_upix, counts = np.unique(upix, return_counts=True)
        self.assertLessEqual(np.max(counts), nmax_per_healpix)

        # Lookup ra,dec in available upix
        upix2 = find_upix(ra, dec, available_upix)
        self.assertTrue(np.all(upix2 == upix))
        nside2, hpix2 = upix2hpix(upix2)
        self.assertTrue(np.all(nside2 == nside))
        self.assertTrue(np.all(hpix2 == hpix))
        for this_nside in np.unique(nside):
            ii = (nside == this_nside)
            this_hpix = radec2hpix(this_nside, ra[ii], dec[ii])
            self.assertTrue(np.all(this_hpix == hpix[ii]))

        # Also works on scalars
        single_upix = find_upix(ra[0], dec[0], available_upix)
        self.assertEqual(single_upix, upix2[0])

        # And even if available_upix isn't properly sorted
        rand.shuffle(available_upix)
        single_upix = find_upix(ra[0], dec[0], available_upix)
        self.assertEqual(single_upix, upix2[0])
        upix3 = find_upix(ra, dec, available_upix)
        self.assertTrue(np.all(upix3 == upix))
