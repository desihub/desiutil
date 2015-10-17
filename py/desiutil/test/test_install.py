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
from subprocess import Popen, PIPE
from shutil import rmtree
from ..install import (dependencies, desiInstall_options, get_product_version,
    get_svn_devstr, git_version,
    most_recent_svn_tag, set_build_type, svn_version)
#
#
#
class TestInstall(unittest.TestCase):
    """Test desiutil.install.
    """
    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__),'t')
        # Suppress log messages.
        logging.getLogger('desiutil').addHandler(logging.NullHandler())
        # Set up a dummy svn repository.
        cls.svn_path = os.path.join(os.path.abspath(cls.data_dir),'svn_test')
        cls.svn_checkout_path = os.path.join(os.path.abspath(cls.data_dir),'svn_test_co')
        p = Popen(['which','svnadmin'],stdout=PIPE,stderr=PIPE)
        out,err = p.communicate()
        cls.has_subversion = p.returncode == 0
        if cls.has_subversion:
            try:
                cls.svn_url = 'file://'+cls.svn_path
                p = Popen(['svnadmin','create',cls.svn_path],stdout=PIPE,stderr=PIPE)
                out,err = p.communicate()
                assert p.returncode == 0
                p = Popen(['svn','mkdir',cls.svn_url+'/trunk',
                    cls.svn_url+'/tags',cls.svn_url+'/branches',
                    '-m',"Create initial structure."],
                    stdout=PIPE,stderr=PIPE)
                out,err = p.communicate()
                assert p.returncode == 0
                p = Popen(['svn','mkdir',cls.svn_url+'/tags/0.0.1',
                    cls.svn_url+'/tags/0.1.0',cls.svn_url+'/tags/0.1.1',
                    cls.svn_url+'/tags/0.2.0',cls.svn_url+'/tags/0.2.1',
                    '-m',"Create tags."],
                    stdout=PIPE,stderr=PIPE)
                out,err = p.communicate()
                assert p.returncode == 0
                p = Popen(['svn','checkout',cls.svn_url, cls.svn_checkout_path],
                    stdout=PIPE,stderr=PIPE)
                out,err = p.communicate()
                assert p.returncode == 0
            except AssertionError:
                cls.has_subversion = False
                rmtree(cls.svn_path)
                rmtree(cls.svn_checkout_path)
        # Create an environment variable pointing to a dummy product.
        if os.path.isdir(cls.svn_checkout_path):
            if 'SVN_TEST_DIR' in os.environ:
                cls.old_svn_test_dir = os.environ['SVN_TEST_DIR']
            else:
                cls.old_svn_test_dir = None
            os.environ['SVN_TEST_DIR'] = cls.svn_checkout_path

    @classmethod
    def tearDownClass(cls):
        # Clean up svn repository.
        if cls.has_subversion:
            rmtree(cls.svn_path)
            rmtree(cls.svn_checkout_path)
        if cls.old_svn_test_dir is None:
            del os.environ['SVN_TEST_DIR']
        else:
            os.environ['SVN_TEST_DIR'] = cls.old_svn_test_dir

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

    def test_desiInstall_options(self):
        """Test the processing of desiInstall command-line arguments.
        """
        # Set a few environment variables for testing purposes.
        env_settings = {
            'MODULESHOME':{'old':None,'new':'/fake/module/directory'},
            'DESI_PRODUCT_ROOT':{'old':None,'new':'/fake/desi/directory'},
            }
        for key in env_settings:
            if key in os.environ:
                env_settings[key]['old'] = os.environ[key]
            os.environ[key] = env_settings[key]['new']
        default_namespace = Namespace(
            bootstrap=False,
            cross_install=False,
            default=False,
            documentation=True,
            force=False,
            force_build_type=False,
            keep=False,
            moduledir=u'',
            moduleshome='/fake/module/directory',
            product=u'NO PACKAGE',
            product_version=u'NO VERSION',
            python=None,
            root='/fake/desi/directory',
            test=False,
            url=u'https://desi.lbl.gov/svn/code',
            username=os.environ['USER'],
            verbose=False)
        options = desiInstall_options([])
        self.assertEqual(options,default_namespace)
        default_namespace.product = 'product'
        default_namespace.product_version = 'version'
        options = desiInstall_options(['product','version'])
        self.assertEqual(options,default_namespace)
        default_namespace.default = True
        options = desiInstall_options(['-d','product','version'])
        self.assertEqual(options,default_namespace)
        # Restore environment.
        for key in env_settings:
            if env_settings[key]['old'] is None:
                del os.environ[key]
            else:
                os.environ[key] = env_settings[key]['old']

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

    def test_get_svn_devstr(self):
        """Test svn revision number determination.
        """
        n = get_svn_devstr('frobulate')
        self.assertEqual(n,'0')
        if self.has_subversion:
            if 'FROBULATE' in os.environ:
                old_frob = os.environ['FROBULATE']
            else:
                old_frob = None
            os.environ['FROBULATE'] = self.data_dir
            n = get_svn_devstr('frobulate')
            self.assertEqual(n,'0')
            if old_frob is None:
                del os.environ['FROBULATE']
            else:
                os.environ['FROBULATE'] = old_frob

    def test_git_version(self):
        """Test automated determination of git version.
        """
        v = git_version('/no/such/executable')
        self.assertEqual(v,'0.0.1.dev')
        v = git_version('false')
        self.assertEqual(v,'0.0.1.dev')
        v = git_version('echo')
        self.assertEqual(v,'describe --tags --dirty --always')

    def test_most_recent_svn_tag(self):
        """Test the processing of svn tag lists.
        """
        if self.has_subversion:
            tag = most_recent_svn_tag(self.svn_url+'/tags')
            self.assertEqual(tag,'0.2.1')
            tag = most_recent_svn_tag(self.svn_url+'/tags',username=os.environ['USER'])
            self.assertEqual(tag,'0.2.1')
            tag = most_recent_svn_tag(self.svn_url+'/branches')
            self.assertEqual(tag,'0.0.0')

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
        v = svn_version("$HeadURL: {0}/tags/0.5.5/README.rst $".format(self.svn_url))
        self.assertEqual(v,'0.5.5', 'Failed to extract version, got {0}.'.format(v))
        v = svn_version("$HeadURL$")
        self.assertEqual(v,'0.0.1.dev', 'Failed to return default version, got {0}.'.format(v))
        if self.has_subversion:
            v = svn_version("$HeadURL: {0}/trunk/README.rst $".format(self.svn_url))
            self.assertEqual(v,'0.2.1.dev2')
            v = svn_version("$HeadURL: {0}/branches/frobulate/README.rst $".format(self.svn_url))
            self.assertEqual(v,'0.2.1.dev2')

if __name__ == '__main__':
    unittest.main()
