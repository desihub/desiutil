# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.iers.
"""
import unittest
from unittest.mock import call, patch, Mock, PropertyMock
# from ..iers import last_tag, version
import desiutil.iers as i


class TestIERS(unittest.TestCase):
    """Test desiutil.iers.
    """

    def setUp(self):
        pass

    def tearDown(self):
        i._iers_is_frozen = False
        # iers_conf.reset()

    def test_update_iers_frozen(self):
        """Test attempt to update a frozen IERS table.
        """
        save_name = os.path.join(self.tmpdir, 'iers.ecsv')
        i.freeze_iers()
        with self.assertRaises(ValueError):
            i.update_iers(save_name)

    def test_update_iers_bad_ext(self):
        """Test save_name extension check.
        """
        save_name = os.path.join(self.tmpdir, 'iers.fits')
        with self.assertRaises(ValueError):
            i.update_iers(save_name)

    def test_update_iers(self):
        """Test updating the IERS table.  Requires a network connection.
        """
        # save_name = os.path.join(self.tmpdir, 'iers.ecsv')
        save_name = resource_filename('desiutil', 'data/iers_frozen.ecsv')
        # i.update_iers(save_name)
        self.assertTrue(os.path.exists(save_name))
        with open(save_name) as i:
            data = i.readlines()
        self.assertIn('# - {data_url: frozen}\n', data)

    def test_freeze_iers(self):
        """Test freezing from package data/.
        """
        i.freeze_iers()
        future = astropy.time.Time('2024-01-01', location=i.get_location())
        lst = future.sidereal_time('apparent')

    def test_freeze_iers_bad_ext(self):
        """Test freezing from package data/ with bad extension.
        """
        with self.assertRaises(ValueError):
            i.freeze_iers('_non_existent_.fits')

    def test_freeze_iers_bad_name(self):
        """Test freezing from package data/ with bad filename.
        """
        with self.assertRaises(ValueError):
            i.freeze_iers('_non_existent_.ecsv')

    def test_freeze_iers_bad_format(self):
        """Test freezing from valid file with wrong format.
        """
        with self.assertRaises(ValueError):
            i.freeze_iers('census.yaml')


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
