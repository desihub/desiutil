# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.depend.
"""
import unittest
import sys
import os
from collections import OrderedDict
from ..depend import (setdep, getdep, hasdep, iterdep, mergedep, removedep,
                      Dependencies, add_dependencies, remove_dependencies)
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
        cls.orig_desi_root = os.getenv('DESI_ROOT')  # value or None

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def tearDown(self):
        # if a test changes DESI_ROOT, set it back to original value
        if self.orig_desi_root is None:
            if 'DESI_ROOT' in os.environ:
                del os.environ['DESI_ROOT']
        else:
            os.environ['DESI_ROOT'] = self.orig_desi_root

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

    def test_mergedep(self):
        """Test merging dependencies from one header to another
        """
        src = dict(
            DEPNAM00='blat', DEPVER00='1.0',
            DEPNAM01='foo', DEPVER01='2.0',
        )
        dst = dict(
            DEPNAM00='biz', DEPVER00='3.0',
            DEPNAM01='bat', DEPVER01='4.0',
        )
        # dependencies from src should be added to dst
        mergedep(src, dst)
        self.assertEqual(getdep(src, 'blat'), getdep(dst, 'blat'))
        self.assertEqual(getdep(src, 'foo'), getdep(dst, 'foo'))

        # ... and the original unique dst versions should still be there
        self.assertEqual(getdep(dst, 'biz'), '3.0')
        self.assertEqual(getdep(dst, 'bat'), '4.0')

        # if conflict='src', a src dependency can replace a dst dependency
        dst = dict(
            DEPNAM00='biz', DEPVER00='3.0',
            DEPNAM01='blat', DEPVER01='4.0',
        )
        mergedep(src, dst, conflict='src')
        self.assertEqual(getdep(src, 'blat'), getdep(dst, 'blat'))
        self.assertEqual(getdep(src, 'foo'), getdep(dst, 'foo'))

        # if conflict='dst', the dst dependency is kept even if in src
        dst = dict(
            DEPNAM00='biz', DEPVER00='3.0',
            DEPNAM01='blat', DEPVER01='4.0',
        )
        mergedep(src, dst, conflict='dst')
        self.assertEqual(getdep(dst, 'blat'), '4.0')  # not '1.0'

        # if conflict='exception', should raise a ValueError
        dst = dict(
            DEPNAM00='biz', DEPVER00='3.0',
            DEPNAM01='blat', DEPVER01='4.0',
        )
        with self.assertRaises(ValueError):
            mergedep(src, dst, conflict='exception')

        # if the same version appears but is consistent, that's ok
        for conflict in ('src', 'dst', 'exception'):
            src = dict(
                DEPNAM00='blat', DEPVER00='1.0',
                DEPNAM01='foo', DEPVER01='2.0',
            )
            dst = dict(
                DEPNAM00='blat', DEPVER00='1.0',
                DEPNAM01='bat', DEPVER01='4.0',
            )
            mergedep(src, dst, conflict=conflict)
            self.assertEqual(getdep(dst, 'blat'), '1.0')
            self.assertEqual(getdep(dst, 'foo'), '2.0')
            self.assertEqual(getdep(dst, 'bat'), '4.0')

        # Unrecognized values of conflict result in a ValueError
        with self.assertRaises(ValueError):
            mergedep(src, dst, conflict='giveup')

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

        # environment variables
        hdr = OrderedDict()
        os.environ['DESI_ROOT'] = '/somewhere/outthere'
        add_dependencies(hdr)
        self.assertTrue(getdep(hdr, 'DESI_ROOT'), '/somewhere/outthere')

        hdr = OrderedDict()
        add_dependencies(hdr, envvar_names=['BLAT'])
        self.assertFalse(hasdep(hdr, 'DESI_ROOT'))  # not in requested envvars
        self.assertTrue(hasdep(hdr, 'BLAT'))
        self.assertEqual(getdep(hdr, 'BLAT'), 'NOT_SET')

        os.environ['BLAT'] = 'foo'
        add_dependencies(hdr, envvar_names=['BLAT'])
        self.assertEqual(getdep(hdr, 'BLAT'), 'foo')

        del os.environ['DESI_ROOT']
        hdr = OrderedDict()
        add_dependencies(hdr)
        self.assertTrue(getdep(hdr, 'DESI_ROOT'), 'NOT_SET')

    def test_remove_dependencies(self):
        """test removedep and remove_dependencies"""

        # add and remove a single dependency
        hdr = dict(HELLO='not a DEPNAMnn/DEPVERnn keyword')
        setdep(hdr, 'blat', 'foo')
        self.assertTrue(hasdep(hdr, 'blat'))
        self.assertTrue('HELLO' in hdr)
        removedep(hdr, 'blat')
        self.assertFalse(hasdep(hdr, 'blat'))
        self.assertTrue('HELLO' in hdr)

        # remove a single dependency in the middle while preserving others
        setdep(hdr, 'blat', 'foo')
        setdep(hdr, 'biz', 'bat')
        setdep(hdr, 'kum', 'quat')
        removedep(hdr, 'biz')
        self.assertTrue(hasdep(hdr, 'blat'))
        self.assertFalse(hasdep(hdr, 'biz'))
        self.assertTrue(hasdep(hdr, 'kum'))
        self.assertTrue('HELLO' in hdr)

        # Add another dependency doesn't trip on the one that was removed
        setdep(hdr, 'abc', 'xyz')
        self.assertTrue(hasdep(hdr, 'blat'))
        self.assertTrue(hasdep(hdr, 'kum'))
        self.assertTrue(hasdep(hdr, 'abc'))
        self.assertTrue('HELLO' in hdr)

        # remove all dependencies
        remove_dependencies(hdr)
        self.assertFalse(hasdep(hdr, 'blat'))
        self.assertFalse(hasdep(hdr, 'biz'))
        self.assertFalse(hasdep(hdr, 'kum'))
        self.assertTrue('HELLO' in hdr)
        for key in hdr:
            self.assertFalse(key.startswith('DEP'))

        with self.assertRaises(ValueError):
            removedep(hdr, 'not_there')
