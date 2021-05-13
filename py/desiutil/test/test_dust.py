# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
desiutil.test.test_dust
=======================

Test desiutil.dust.
"""
import unittest
from unittest.mock import patch, call
import os
import numpy as np
from .. import dust
#import desiutil.dust as dust
from pkg_resources import resource_filename
from astropy.coordinates import SkyCoord
from astropy import units as u


class TestDust(unittest.TestCase):
    """Test desiutil.dust.
    """

    def setUp(self):
        self.mapdir = resource_filename('desiutil.test', 't')
        # ADM these RAs/DECs are set to be in the 0-10 pixel column
        # ADM in the dust map files to correspond to
        # ADM the test data made by make_testmaps.py
        # ADM the corresponding b values are
        # [ 0.00606523  0.00370056 -0.00511865  0.00139846 -0.0003694 ]
        # ADM to test both the SGP and the NGP
        self.ra = np.array([84.56347552,  88.25858593,
                            85.18114653,  84.04246538, 83.22215524])
        self.dec = np.array([32.14649459,  26.61522843,  30.10225407,
                             32.34100748, 33.22330424])
        self.ebv = np.array([1.45868814,  1.59562695,  1.78565359,
                             0.95239526,  0.87789094], dtype='<f4')

    def test_ebv(self):
        """Test E(B-V) map code gives correct results.
        """
        ebvtest = dust.ebv(self.ra, self.dec,
                           mapdir=self.mapdir).astype('<f4')
        self.assertTrue(np.all(ebvtest == self.ebv))

    def test_ebv_scaling(self):
        """Test E(B-V) map code default scaling is 1.
        """
        # ADM a useful scaling to test as it's the Schlafly/Finkbeiner (2011) value
        scaling = 0.86
        ebvtest1 = dust.ebv(self.ra, self.dec,
                            mapdir=self.mapdir, scaling=scaling)
        ebvtest2 = scaling*dust.ebv(self.ra, self.dec,
                                    mapdir=self.mapdir)
        # ADM 1e-7 is fine. We don't know dust values to 0.00001%
        self.assertTrue(np.all(np.abs(ebvtest1-ebvtest2) < 1e-7))

    def test_inputs(self):
        """Test E(B-V) code works with alternative input formats.
        """
        # ADM tuple (and scalar) format
        # ADM with no interpolation and a strange fk5 system
        ebvtest1 = dust.ebv((self.ra[0], self.dec[0]), frame='fk5j2000',
                            mapdir=self.mapdir, interpolate=False).astype('<f4')

        # ADM astropy Sky Coordinate format
        # ADM with no interpolation and a strange fk5 system
        cobjs = SkyCoord(self.ra*u.degree, self.dec*u.degree, frame='fk5')
        ebvtest2 = dust.ebv(cobjs,
                            mapdir=self.mapdir, interpolate=False).astype('<f4')

        self.assertTrue(ebvtest2[0] == ebvtest1)

    @patch('desiutil.dust.log')
    def test_class(self, mock_logger):
        """Test E(B-V) class initialization fails appropriately.
        """
        # ADM count the tests that work
        testcnt = 0

        # ADM initially unset the DUST_DIR environment variable
        dustdir = os.environ.get('DUST_DIR')
        if dustdir is not None:
            del os.environ['DUST_DIR']

        # ADM check calling the class without 'DUST_DIR' or a map directory
        with self.assertRaisesRegex(ValueError, r'Pass mapdir or set \$DUST_DIR'):
            ss = dust.SFDMap()

        # ADM reset the DUST_DIR environment variable
        if dustdir is not None:
            os.environ["DUST_DIR"] = dustdir

        # ADM test calling the class with a non-existent directory
        with self.assertRaisesRegex(ValueError, r'Dust maps not found in directory blatfoo'):
            ss = dust.SFDMap(mapdir='blatfoo')

        mock_logger.critical.assert_has_calls([call('Pass mapdir or set $DUST_DIR'),
                                               call('Dust maps not found in directory blatfoo')])

    def test_extinction(self):
        """Test ext_odonnel and ext_ccm functions"""
        wave = np.arange(2000, 10001, 100)
        ext_odl_31 = dust.ext_odonnell(wave, Rv=3.1)
        ext_odl_33 = dust.ext_odonnell(wave, Rv=3.3)
        ext_ccm_31 = dust.ext_ccm(wave, Rv=3.1)
        ext_ccm_33 = dust.ext_ccm(wave, Rv=3.3)

        # Sanity check on ranges
        self.assertTrue(np.all(0.4 < ext_odl_31) and np.all(ext_odl_31 < 4.0))
        self.assertTrue(np.all(0.4 < ext_odl_33) and np.all(ext_odl_33 < 4.0))
        self.assertTrue(np.all(0.4 < ext_ccm_31) and np.all(ext_ccm_31 < 4.0))
        self.assertTrue(np.all(0.4 < ext_ccm_33) and np.all(ext_ccm_33 < 4.0))

        # Changing Rv should change answer
        self.assertTrue(np.all(ext_odl_31 != ext_odl_33))
        self.assertTrue(np.all(ext_ccm_31 != ext_ccm_33))

        # Odonnell == CCM for some but not all wavelengths
        self.assertTrue(np.any(ext_odl_31 == ext_ccm_31))
        self.assertTrue(np.any(ext_odl_31 != ext_ccm_31))
        self.assertTrue(np.any(ext_odl_33 == ext_ccm_33))
        self.assertTrue(np.any(ext_odl_33 != ext_ccm_33))

    def test_total_to_selective(self):
        """Test extinction total_to_selective_ratio"""

        #- test valid options with upper and lowercase
        for band in ['G', 'R', 'Z']:
            for photsys in ['N', 'S']:
                rb1 = dust.extinction_total_to_selective_ratio(band.upper(), photsys.upper())
                rb2 = dust.extinction_total_to_selective_ratio(band.lower(), photsys.lower())
                self.assertEqual(rb1, rb2)

        #- North and South should be different
        for band in ['G', 'R', 'Z']:
            rb1 = dust.extinction_total_to_selective_ratio(band, 'N')
            rb2 = dust.extinction_total_to_selective_ratio(band, 'S')
            self.assertNotEqual(rb1, rb2)

        #- B is not a supported band (G,R,Z)
        with self.assertRaises(AssertionError):
            rb = dust.extinction_total_to_selective_ratio('B', 'N')

        #- Q is not a valid photsys (N,S)
        with self.assertRaises(AssertionError):
            rb = dust.extinction_total_to_selective_ratio('G', 'Q')

    def test_dust_transmission(self) :
        dust.dust_transmission(np.linspace(3600,9000,1000),0.1)

    def test_gaia_extinction(self) :
        dust.gaia_extinction(g=14.,bp=14.,rp=14.,ebv_sfd=0.4)

    def test_mwdust_transmission(self):
        ebv = np.array([0.0, 0.1, 0.2, 0.3])
        for band in ['G', 'R', 'Z']:
            for photsys in ['N', 'S']:
                t = dust.mwdust_transmission(ebv, band, photsys)
                self.assertEqual(len(t), len(ebv))
                self.assertEqual(t[0], 1.0)
                self.assertTrue(np.all(np.diff(t) < 0))

        #- test scalar/vector combinations
        t = dust.mwdust_transmission(ebv, 'R', 'N')
        for i in range(len(t)):
            self.assertEqual(t[i], dust.mwdust_transmission(ebv[i], 'R', 'N'))

        tn = dust.mwdust_transmission(ebv, 'R', ['N']*len(ebv))
        ts = dust.mwdust_transmission(ebv, 'R', ['S']*len(ebv))
        self.assertEqual(len(tn), len(ebv))
        self.assertEqual(len(ts), len(ebv))
        #- N vs. S should be different where ebv>0
        ii = (ebv>0)
        self.assertTrue(np.all(tn[ii] != ts[ii]))

        #- array photsys must have ebv array of same length
        with self.assertRaises(ValueError):
            dust.mwdust_transmission(0.1, 'G', ['N', 'S'])

        with self.assertRaises(ValueError):
            dust.mwdust_transmission([0.1, 0.2, 0.3], 'G', ['N', 'S'])

def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
