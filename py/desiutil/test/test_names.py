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
        self.assertTrue((outnames == correct_names).all())

        # Test array conversion
        outnames = radec_to_desiname(np.array(ras),
                                     np.array(decs))
        self.assertTrue((outnames == correct_names).all())

    def test_radec_to_desiname_bad_values(self):
        """Test exceptions when running radec_to_desiname with bad values.
        """
        ras = [6.2457354547234, 23.914121939862518, 36.23454570972834,
               235.25235223446, 99.9999999999999]
        decs = [29.974787585945496, -42.945872347904356, -0.9968423456,
                8.45677345352345, 89.234958294953]

        original_ra = ras[2]
        for message, value in [("NaN values detected in target_ra!", np.nan),
                               ("Infinite values detected in target_ra!", np.inf),
                               ("RA not in range [0, 360) detected in target_ra!", -23.914121939862518),
                               ("RA not in range [0, 360) detected in target_ra!", 360.23454570972834)]:
            ras[2] = value
            with self.assertRaises(ValueError) as e:
                outnames = radec_to_desiname(ras, decs)
            self.assertEqual(str(e.exception), message)

        ras[2] = original_ra

        original_dec = decs[2]
        for message, value in [("NaN values detected in target_dec!", np.nan),
                               ("Infinite values detected in target_dec!", np.inf),
                               ("Dec not in range [-90, 90] detected in target_dec!", -90.9968423456),
                               ("Dec not in range [-90, 90] detected in target_dec!", 90.9968423456)]:
            decs[2] = value
            with self.assertRaises(ValueError) as e:
                outnames = radec_to_desiname(ras, decs)
            self.assertEqual(str(e.exception), message)

        decs[2] = original_dec
