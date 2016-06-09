# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.git.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import unittest
from desiutil import depend

try:
    from astropy.io import fits
    test_fits_header = True
except ImportError:
    test_fits_header = False

class TestDepend(unittest.TestCase):
    """Test desiutil.depend
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_functions(self):
        hdr = dict()
        depend.setdep(hdr, 'blat', '1.2.3')
        self.assertEqual(depend.getdep(hdr, 'blat'), '1.2.3')
        self.assertTrue(depend.hasdep(hdr, 'blat'))
        
        with self.assertRaises(KeyError):
            depend.getdep(hdr, 'foo')
            
    @unittest.skipUnless(test_fits_header, 'requires astropy.io.fits')
    def test_fits_header(self):
        hdr = fits.Header()
        depend.setdep(hdr, 'blat', '1.2.3')
        self.assertEqual(depend.getdep(hdr, 'blat'), '1.2.3')
        self.assertTrue(depend.hasdep(hdr, 'blat'))
        self.assertFalse(depend.hasdep(hdr, 'zoom'))
        
        with self.assertRaises(KeyError):
            depend.getdep(hdr, 'foo')

    def test_update(self):
        hdr = dict()
        depend.setdep(hdr, 'blat', '1.0')
        self.assertEqual(depend.getdep(hdr, 'blat'), '1.0')
        depend.setdep(hdr, 'blat', '2.0')
        self.assertEqual(depend.getdep(hdr, 'blat'), '2.0')
        self.assertNotIn('DEPNAM01', hdr)
        depend.setdep(hdr, 'foo', '3.0')
        self.assertEqual(hdr['DEPNAM01'], 'foo')
        self.assertEqual(hdr['DEPVER01'], '3.0')

    def test_class(self):
        hdr = dict()
        x = depend.Dependencies(hdr)
        x['blat'] = '1.2.3'
        x['foo'] = '0.1'
        self.assertEqual(x['blat'], hdr['DEPVER00'])
        self.assertEqual(x['foo'], hdr['DEPVER01'])
        for name, version in x.items():
            self.assertEqual(version, x[name])
            
        for name in x:
            self.assertEqual(x[name], depend.getdep(hdr, name))

if __name__ == '__main__':
    unittest.main()