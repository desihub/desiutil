# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.names.
"""
import unittest
import numpy as np
from ..names import radec_to_desiname


class TestNames(unittest.TestCase):
    """Test desiutil.names
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_radec_to_desiname(self):
        """Test computation of desiname.
        """
        ras = [6.2457354547234, 23.914121939862518, 36.23454570972834,
               235.25235223446, 99.9999999999999]
        decs = [29.974787585945496, -42.945872347904356, -0.9968423456,
                8.45677345352345, 89.234958294953]
        correct_names = np.array(['DESI J006.2457+29.9747',
                                  'DESI J023.9141-42.9458',
                                  'DESI J036.2345-00.9968',
                                  'DESI J235.2523+08.4567',
                                  'DESI J099.9999+89.2349'])
        # Test scalar conversion
        for ra, dec, correct_name in zip(ras, decs, correct_names):
            outname = radec_to_desiname(ra, dec)
            self.assertEqual(outname, correct_name)

        # Test list conversion
        outnames = radec_to_desiname(ras, decs)
        self.assertTrue(np.alltrue(outnames == correct_names))

        # Test array conversion
        outnames = radec_to_desiname(np.array(ras),
                                     np.array(decs))
        self.assertTrue(np.alltrue(outnames == correct_names))

    def test_radec_to_desiname_bad_values(self):
        """Test exceptions when running radec_to_desiname with bad values.
        """
        ras = [6.2457354547234, 23.914121939862518, 36.23454570972834,
               235.25235223446, 99.9999999999999]
        decs = [29.974787585945496, -42.945872347904356, -0.9968423456,
                8.45677345352345, 89.234958294953]
        ras[2] = np.nan
        with self.assertRaises(ValueError) as e:
            outnames = radec_to_desiname(ras, decs)
        self.assertEqual(str(e.exception), "NaN values detected in target_ra!")

        ras[2] = np.inf
        with self.assertRaises(ValueError) as e:
            outnames = radec_to_desiname(ras, decs)
        self.assertEqual(str(e.exception), "Infinite values detected in target_ra!")
