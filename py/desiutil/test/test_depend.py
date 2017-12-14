# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.depend.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import unittest
import sys
from collections import OrderedDict
from ..depend import (setdep, getdep, hasdep, iterdep, Dependencies,
                      add_dependencies)
from .. import __version__ as desiutil_version

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

    def test_setdep(self):
        """Test function that sets dependency keywords.
        """
        hdr = dict()
        setdep(hdr, 'blat', '1.2.3')
        self.assertEqual(hdr['DEPNAM00'], 'blat')
        self.assertEqual(hdr['DEPVER00'], '1.2.3')
        setdep(hdr, 'foo', '2.3.4')
        self.assertEqual(hdr['DEPNAM01'], 'foo')
        self.assertEqual(hdr['DEPVER01'], '2.3.4')
        setdep(hdr, 'blat', '3.4.5')
        self.assertEqual(hdr['DEPNAM00'], 'blat')
        self.assertEqual(hdr['DEPVER00'], '3.4.5')
        setdep(hdr, 'bar', '7.8.9')
        setdep(hdr, 'baz', '9.8.7')
        setdep(hdr, 'foo', '4.3.2')
        self.assertEqual(hdr['DEPNAM01'], 'foo')
        self.assertEqual(hdr['DEPVER01'], '4.3.2')
        hdr = dict()
        with self.assertRaises(IndexError):
            for i in range(101):
                setdep(hdr, 'test{0:03d}'.format(i), "v{0:d}.0.1".format(i))

    def test_getdep(self):
        """Test function that gets dependency values.
        """
        hdr = dict()
        for i in range(10):
            setdep(hdr, 'test{0:03d}'.format(i), "v{0:d}.0.1".format(i))
        self.assertEqual(hdr['DEPNAM00'], 'test000')
        self.assertEqual(hdr['DEPVER00'], 'v0.0.1')
        self.assertEqual(getdep(hdr, 'test005'), 'v5.0.1')
        hdr = dict()
        for i in range(10):
            hdr["DEPNAM{0:02d}".format(i+1)] = "test{0:03d}".format(i+1)
            hdr["DEPVER{0:02d}".format(i+1)] = "v{0:d}.0.1".format(i+1)
        self.assertEqual(getdep(hdr, 'test005'), 'v5.0.1')
        with self.assertRaises(KeyError):
            foo = getdep(hdr, 'test100')

    def test_hasdep(self):
        """Test function that checks for the existence of a dependency.
        """
        hdr = dict()
        for i in range(10):
            hdr["DEPNAM{0:02d}".format(i+1)] = "test{0:03d}".format(i+1)
            hdr["DEPVER{0:02d}".format(i+1)] = "v{0:d}.0.1".format(i+1)
        self.assertTrue(hasdep(hdr, 'test001'))
        self.assertTrue(hasdep(hdr, 'test010'))
        self.assertFalse(hasdep(hdr, 'test020'))

    @unittest.skipUnless(test_fits_header, 'requires astropy.io.fits')
    def test_fits_header(self):
        """Test dependency functions with an actual FITS header.
        """
        hdr = fits.Header()
        setdep(hdr, 'blat', '1.2.3')
        self.assertEqual(getdep(hdr, 'blat'), '1.2.3')
        self.assertTrue(hasdep(hdr, 'blat'))
        self.assertFalse(hasdep(hdr, 'zoom'))
        setdep(hdr, 'blat', '1.5')
        self.assertEqual(getdep(hdr, 'blat'), '1.5')
        self.assertTrue(hasdep(hdr, 'blat'))

        with self.assertRaises(KeyError):
            getdep(hdr, 'foo')

    def test_update(self):
        """Test updates of dependencies.
        """
        hdr = dict()
        setdep(hdr, 'blat', '1.0')
        self.assertEqual(getdep(hdr, 'blat'), '1.0')
        setdep(hdr, 'blat', '2.0')
        self.assertEqual(getdep(hdr, 'blat'), '2.0')
        self.assertNotIn('DEPNAM01', hdr)
        setdep(hdr, 'foo', '3.0')
        self.assertEqual(hdr['DEPNAM01'], 'foo')
        self.assertEqual(hdr['DEPVER01'], '3.0')

    def test_iter(self):
        """Test iteration methods.
        """
        hdr = dict()
        for i in range(100):
            hdr["DEPNAM{0:02d}".format(i)] = "test{0:03d}".format(i)
            hdr["DEPVER{0:02d}".format(i)] = "v{0:d}.0.1".format(i)
        y = Dependencies(hdr)
        for name in y:
            self.assertEqual(y[name], getdep(hdr, name))

        for name, version in y.items():
            self.assertEqual(version, getdep(hdr, name))

        for name, version in iterdep(hdr):
            self.assertEqual(version, getdep(hdr, name))
        #
        # Test dependency index starting from one.
        #
        hdr = dict()
        for j in range(1, 20):
            hdr["DEPNAM{0:02d}".format(i)] = "test{0:03d}".format(i)
            hdr["DEPVER{0:02d}".format(i)] = "v{0:d}.0.1".format(i)
        y = Dependencies(hdr)
        for name in y:
            self.assertEqual(y[name], getdep(hdr, name))

        for name, version in y.items():
            self.assertEqual(version, getdep(hdr, name))

        for name, version in iterdep(hdr):
            self.assertEqual(version, getdep(hdr, name))


    def test_class(self):
        """Test the Dependencies object.
        """
        d = Dependencies()
        self.assertTrue(isinstance(d.header, OrderedDict))
        hdr = dict()
        x = Dependencies(hdr)
        x['blat'] = '1.2.3'
        x['foo'] = '0.1'
        self.assertEqual(x['blat'], hdr['DEPVER00'])
        self.assertEqual(x['foo'], hdr['DEPVER01'])
        for name, version in x.items():
            self.assertEqual(version, x[name])

        for name in x:
            self.assertEqual(x[name], getdep(hdr, name))

    def test_add_dependencies(self):
        """Test add_dependencies function.
        """
        hdr = OrderedDict()
        add_dependencies(hdr, long_python=True)
        self.assertEqual(getdep(hdr, 'python'),
                         sys.version.replace('\n', ' '))
        hdr = OrderedDict()
        add_dependencies(hdr)
        self.assertEqual(getdep(hdr, 'python'),
                         ".".join(map(str, sys.version_info[0:3])))
        self.assertEqual(getdep(hdr, 'desiutil'), desiutil_version)
        import numpy
        add_dependencies(hdr)
        self.assertEqual(getdep(hdr, 'numpy'), numpy.__version__)
        # ok, but no action
        add_dependencies(hdr, ['blatbar', 'quatlarm'])
        self.assertFalse(hasdep(hdr, 'blatbar'))
        self.assertFalse(hasdep(hdr, 'quatlarm'))

        # no .__version__
        add_dependencies(hdr, ['os.path', 'unittest', 'sys'])
        self.assertTrue(hasdep(hdr, 'os.path'))
        self.assertTrue(getdep(hdr, 'os.path').startswith('unknown'))
        self.assertTrue(hasdep(hdr, 'unittest'))
        self.assertTrue(getdep(hdr, 'unittest').startswith('unknown'))
        self.assertTrue(hasdep(hdr, 'sys'))
        self.assertTrue(getdep(hdr, 'sys').startswith('unknown'))


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
