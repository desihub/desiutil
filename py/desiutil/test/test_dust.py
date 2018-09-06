# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
desiutil.test.test_dust
=======================

Test desiutil.dust.
"""
from __future__ import absolute_import, division, unicode_literals
# The line above will help with 2to3 support.
import unittest
import os
import numpy as np
from .. import dust
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

    def test_class(self):
        """Test E(B-V) class initialization fails appropriately.
        """
        # ADM count the tests that work
        testcnt = 0

        # ADM initially unset the DUST_DIR environment variable
        dustdir = os.environ.get('DUST_DIR')
        if dustdir is not None:
            del os.environ['DUST_DIR']

        # ADM check calling the class without 'DUST_DIR' or a map directory
        try: 
            ss = dust.SFDMap()
        except ValueError:
            testcnt += 1

        # ADM reset the DUST_DIR environment variable
        if dustdir is not None:
            os.environ["DUST_DIR"] = dustdir

        # ADM test calling the class with a non-existent directory
        try: 
            ss = dust.SFDMap(mapdir='blatfoo')
        except ValueError:
            testcnt += 1

        # ADM assert that the tests worked 
        self.assertTrue(testcnt == 2)

def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
