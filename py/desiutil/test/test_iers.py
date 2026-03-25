# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.iers.
"""
import unittest
import shutil
import tempfile
from unittest.mock import call, patch
from astropy import __version__ as AstropyVersion
import astropy.units as u
import astropy.utils.iers
from astropy.time import Time
import desiutil.iers as i
#
# This import will trigger a download of the leap second file.
#
from astropy.coordinates import EarthLocation


class TestIERS(unittest.TestCase):
    """Test desiutil.iers.
    """

    @classmethod
    def setUpClass(cls):
        # Create a temporary directory.
        cls.tmpdir = tempfile.mkdtemp()
        cls.ap2 = int(AstropyVersion.split('.')[0])
        # Needed for time tests.
        cls.location = EarthLocation.from_geodetic(lat=31.963972222*u.deg,
                                                   lon=-111.599336111*u.deg,
                                                   height=2120*u.m)

    @classmethod
    def tearDownClass(cls):
        # Remove the directory after the test.
        shutil.rmtree(cls.tmpdir)

    def setUp(self):
        # Reset all configuration parameteters to default.
        astropy.utils.iers.conf.reload()

    def tearDown(self):
        i._iers_is_frozen = False
        # iers_conf.reset()

    @patch('desiutil.iers.get_logger')
    def test_freeze_iers(self, mock_logger):
        """Test freezing from package data/.
        """
        i.freeze_iers()
        future = Time('2024-01-01', location=self.location)
        lst = future.sidereal_time('apparent')
        self.assertFalse(astropy.utils.iers.conf.auto_download)
        self.assertIsNone(astropy.utils.iers.conf.auto_max_age)
        self.assertEqual(astropy.utils.iers.conf.iers_auto_url, 'frozen')
        self.assertEqual(astropy.utils.iers.conf.iers_auto_url_mirror, 'frozen')
        self.assertEqual(astropy.utils.iers.conf.iers_degraded_accuracy, 'ignore')
        mock_logger().info.assert_has_calls([call('Freezing IERS table used by astropy time, coordinates.')])

    @patch('desiutil.iers.get_logger')
    def test_freeze_iers_ignore_warnings(self, mock_logger):
        """Test freezing from package data/, but allow warnings.
        """
        i.freeze_iers(ignore_warnings=False)
        future = Time('2024-01-01', location=self.location)
        lst = future.sidereal_time('apparent')
        self.assertFalse(astropy.utils.iers.conf.auto_download)
        self.assertIsNone(astropy.utils.iers.conf.auto_max_age)
        self.assertEqual(astropy.utils.iers.conf.iers_auto_url, 'frozen')
        self.assertEqual(astropy.utils.iers.conf.iers_auto_url_mirror, 'frozen')
        self.assertEqual(astropy.utils.iers.conf.iers_degraded_accuracy, 'warn')
        mock_logger().info.assert_has_calls([call('Freezing IERS table used by astropy time, coordinates.')])

    @patch('desiutil.iers.get_logger')
    def test_freeze_iers_again(self, mock_logger):
        """Test freezing twice.
        """
        i._iers_is_frozen = True
        i.freeze_iers()
        mock_logger().debug.assert_has_calls([call('IERS table already frozen.')])

