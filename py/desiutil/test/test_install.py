# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
test util.install
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
#
import os
import unittest
from argparse import Namespace
from ..install import dependencies, get_product_version, version
#
class TestInstall(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__),'t')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_dependencies(self):
        """Test dependency processing.
        """
        # Raise ValueError if file doesn't exist:
        with self.assertRaises(ValueError) as cm:
            dependencies("foo/bar/baz.module")
        self.assertEqual(cm.exception.message, "Modulefile foo/bar/baz.module does not exist!")
        # Manipulate the environment.
        nersc_host = None
        if 'NERSC_HOST' in os.environ:
            # Temporarily delete the NERSC_HOST variable.
            nersc_host = os.environ['NERSC_HOST']
            del os.environ['NERSC_HOST']
        # Standard dependencies.
        deps = dependencies(os.path.join(self.data_dir,'generic_dependencies.txt'))
        self.assertEqual(set(deps),set(['astropy', 'desiutil/1.0.0']))
        # NERSC dependencies.
        if nersc_host is None:
            # Temporarily create a fake NERSC host
            os.environ['NERSC_HOST'] = 'FAKE'
        else:
            # Restore original value
            os.environ['NERSC_HOST'] = nersc_host
        deps = dependencies(os.path.join(self.data_dir,'nersc_dependencies.txt'))
        self.assertEqual(set(deps),set(['astropy-hpcp', 'setuptools-hpcp', 'desiutil/1.0.0']))
        # Clean up the environment.
        if os.environ['NERSC_HOST'] == 'FAKE':
            del os.environ['NERSC_HOST']

    def test_get_product_version(self):
        """Test resolution of product/version input.
        """
        pv = Namespace(product='foo',product_version='bar')
        with self.assertRaises(ValueError) as cm:
            out = get_product_version(pv)
        self.assertEqual(cm.exception.message, "Could not determine the exact location of foo!")
        pv = Namespace(product='desiutil',product_version='1.0.0')
        out = get_product_version(pv)
        self.assertEqual(out, (u'desihub/desiutil', 'desiutil', '1.0.0'))
        pv = Namespace(product='desihub/desispec',product_version='2.0.0')
        out = get_product_version(pv)
        self.assertEqual(out, (u'desihub/desispec', 'desispec', '2.0.0'))

    def test_version(self):
        """Test version parser.
        """
        v = version("$HeadURL: https://desi.lbl.gov/svn/code/tools/desiUtil/tags/0.5.5/py/desiutil/test/test_install.py $")
        self.assertEqual(v,'0.5.5', 'Failed to extract version, got {0}.'.format(v))
        v = version("$HeadURL$")
        self.assertEqual(v,'0.0.1.dev', 'Failed to return default version, got {0}.'.format(v))

if __name__ == '__main__':
    unittest.main()
