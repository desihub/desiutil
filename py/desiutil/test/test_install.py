# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
test util.install
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
#
import os
import logging
import unittest
from argparse import Namespace
from ..install import dependencies, get_product_version, set_build_type, svn_version
#
class TestInstall(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__),'t')
        # Suppress log messages.
        logging.getLogger('desiutil').addHandler(logging.NullHandler())

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

    def test_set_build_type(self):
        """Test the determination of the build type.
        """
        bt = set_build_type(self.data_dir)
        self.assertEqual(bt,set(['plain']))
        bt = set_build_type(self.data_dir,force=True)
        self.assertEqual(bt,set(['plain','make']))
        # Create temporary files
        tempfiles = {'Makefile':'make','setup.py':'py'}
        for t in tempfiles:
            tempfile = os.path.join(self.data_dir,t)
            with open(tempfile,'w') as tf:
                tf.write('Temporary file.\n')
            bt = set_build_type(self.data_dir)
            self.assertEqual(bt,set(['plain',tempfiles[t]]))
            os.remove(tempfile)
        # Create temporary directories
        tempdirs = {'src':'src'}
        for t in tempdirs:
            tempdir = os.path.join(self.data_dir,t)
            os.mkdir(tempdir)
            bt = set_build_type(self.data_dir)
            self.assertEqual(bt,set(['plain',tempdirs[t]]))
            os.rmdir(tempdir)

    def test_svn_version(self):
        """Test svn version parser.
        """
        v = svn_version("$HeadURL: https://desi.lbl.gov/svn/code/tools/desiUtil/tags/0.5.5/py/desiutil/test/test_install.py $")
        self.assertEqual(v,'0.5.5', 'Failed to extract version, got {0}.'.format(v))
        v = svn_version("$HeadURL$")
        self.assertEqual(v,'0.0.1.dev', 'Failed to return default version, got {0}.'.format(v))

if __name__ == '__main__':
    unittest.main()
