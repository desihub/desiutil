# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.iers.
"""
import unittest
import datetime
import os
import shutil
import tempfile
from unittest.mock import call, patch, MagicMock
from importlib.resources import files
from packaging.version import Version
from astropy import __version__ as AstropyVersion
import astropy.units as u
import astropy.utils.iers
from astropy.table import QTable
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
        cls.astropy_version = Version(AstropyVersion)
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
    def test_update_iers_frozen(self, mock_logger):
        """Test attempt to update a frozen IERS table.
        """
        save_name = os.path.join(self.tmpdir, 'iers.ecsv')
        i.freeze_iers()
        with self.assertRaises(ValueError):
            i.update_iers(save_name)
        mock_logger().info.assert_has_calls([call('Freezing IERS table used by astropy time, coordinates.')])

    @patch('desiutil.iers.get_logger')
    def test_update_iers_bad_ext(self, mock_logger):
        """Test save_name extension check.
        """
        save_name = os.path.join(self.tmpdir, 'iers.fits')
        with self.assertRaises(ValueError):
            i.update_iers(save_name)

    @patch('desiutil.iers.get_logger')
    def test_update_iers_file(self, mock_logger):
        """Check the existing frozen file for correctness.
        """
        # save_name = os.path.join(self.tmpdir, 'iers.ecsv')
        save_name = str(files('desiutil') / 'data' / 'iers_frozen.ecsv')
        # i.update_iers(save_name)
        self.assertTrue(os.path.exists(save_name))
        with open(save_name) as s:
            data = s.readlines()
        self.assertIn('# - {data_url: frozen}\n', data)
        # mock_logger().info.assert_has_calls([call('Freezing IERS table used by astropy time, coordinates.')])

    @patch('desiutil.iers.Time')
    @patch.object(astropy.utils.iers.IERS_A, 'open')
    @patch('desiutil.iers.get_logger')
    def test_update_iers(self, mock_logger, mock_iers, mock_time):
        """Test updating the IERS table.
        """
        real_name = str(files('desiutil') / 'data' / 'iers_frozen.ecsv')
        t = QTable.read(real_name, format='ascii.ecsv')
        mock_iers.return_value = t
        d = MagicMock()
        d.datetime = datetime.datetime(2018, 5, 12, 0, 0)
        mock_time.return_value = d
        save_name = os.path.join(self.tmpdir, 'iers.ecsv')
        i.update_iers(save_name)
        self.assertTrue(os.path.exists(save_name))
        with open(save_name) as s:
            data = s.readlines()
        if self.ap2 < 3 or self.ap2 > 6:
            self.assertIn('# - {data_url: frozen}\n', data)
        else:
            self.assertIn('#   data_url: frozen\n', data)
        mock_iers.assert_has_calls([call(astropy.utils.iers.conf.iers_auto_url)])
        mock_time.assert_has_calls([call(t["MJD"][-1], format='mjd')])
        mock_logger().info.assert_has_calls([call('Updating to current IERS-A table with coverage up to %s.', datetime.date(2018, 5, 12)),
                                             call('Wrote updated table to %s.', save_name)],
                                            any_order=True)

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

    @patch('desiutil.iers._need_frozen_table')
    @patch('desiutil.iers.get_logger')
    def test_freeze_iers_bad_ext(self, mock_logger, mock_need_table):
        """Test freezing from package data/ with bad extension.
        """
        mock_need_table.return_value = True
        with self.assertRaises(ValueError):
            i.freeze_iers('_non_existent_.fits')
        mock_logger().info.assert_has_calls([call('Freezing IERS table used by astropy time, coordinates.')])

    @patch('desiutil.iers._need_frozen_table')
    @patch('desiutil.iers.get_logger')
    def test_freeze_iers_bad_name(self, mock_logger, mock_need_table):
        """Test freezing from package data/ with bad filename.
        """
        mock_need_table.return_value = True
        with self.assertRaises(ValueError):
            i.freeze_iers('_non_existent_.ecsv')
        mock_logger().info.assert_has_calls([call('Freezing IERS table used by astropy time, coordinates.')])

    @patch('desiutil.iers._need_frozen_table')
    @patch('desiutil.iers.get_logger')
    def test_freeze_iers_bad_format(self, mock_logger, mock_need_table):
        """Test freezing from valid file with wrong format.
        """
        mock_need_table.return_value = True
        with self.assertRaises(ValueError):
            i.freeze_iers('census.yaml')
        mock_logger().info.assert_has_calls([call('Freezing IERS table used by astropy time, coordinates.')])
