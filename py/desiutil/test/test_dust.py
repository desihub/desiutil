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

class TestDust(unittest.TestCase):
    """Test desiutil.dust.
    """

    def setUp(self):
        n = 10
        self.ra = np.linspace(0, 3, n) - 1.5
        self.dec = np.linspace(0, 3, n) - 1.5
        self.ebv = np.array([0.027391933, 0.024605898, 0.027694058,
                             0.040832218, 0.036266338, 0.033251308,
                             0.032212332, 0.031226717, 0.028192421,
                             0.027784575], dtype='<f4')


    @unittest.skipIf('DUST_DIR' not in os.environ,
                     "Skipping test that requires DUST_DIR to point to SFD maps")
    def test_ebv(self):
        """Test E(B-V) map code gives correct results
        """
        ebvtest = dust.ebv(self.ra,self.dec).astype('<f4')
        self.assertTrue(np.all(ebvtest==self.ebv))

    @unittest.skipIf('DUST_DIR' not in os.environ,
                     "Skipping test that requires DUST_DIR to point to SFD maps")
    def test_ebv_scaling(self):
        """Test E(B-V) map code default scaling is 1
        """
        #ADM a useful scaling to test as it's the Schlafly/Finkbeiner (2011) value
        scaling = 0.86
        ebvtest1 = dust.ebv(self.ra,self.dec,scaling=scaling)
        ebvtest2 = scaling*dust.ebv(self.ra,self.dec)
        self.assertTrue(np.all(np.abs(ebvtest1-ebvtest2) < 1e-8))

def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
