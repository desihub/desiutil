# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.install.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
import logging
from os import chdir, environ, getcwd, mkdir, remove, rmdir
from os.path import dirname, isdir, join
from shutil import rmtree
from argparse import Namespace
from ..install import DesiInstall, DesiInstallException, dependencies


class TestInstall(unittest.TestCase):
    """Test desiutil.install.
    """

    @classmethod
    def setUpClass(cls):
        # Data directory
        cls.data_dir = join(dirname(__file__), 't')

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        # Create a "fresh" DesiInstall object for every test.
        self.desiInstall = DesiInstall(test=True)

    def tearDown(self):
        pass

    def assertLog(self, order=-1, message=''):
        """Examine the log messages.
        """
        log = logging.getLogger('desiutil.install')
        self.assertEqual(log.handlers[0].buffer[order].msg, message)

    def test_dependencies(self):
        """Test dependency processing.
        """
        # Raise ValueError if file doesn't exist:
        with self.assertRaises(ValueError) as cm:
            dependencies("foo/bar/baz.module")
        self.assertEqual(str(cm.exception),
                         "Modulefile foo/bar/baz.module does not exist!")
        # Manipulate the environment.
        nersc_host = None
        if 'NERSC_HOST' in environ:
            # Temporarily delete the NERSC_HOST variable.
            nersc_host = environ['NERSC_HOST']
            del environ['NERSC_HOST']
        # Standard dependencies.
        deps = dependencies(join(self.data_dir, 'generic_dependencies.txt'))
        self.assertEqual(set(deps), set(['astropy', 'desiutil/1.0.0']))
        # NERSC dependencies.
        if nersc_host is None:
            # Temporarily create a fake NERSC host
            environ['NERSC_HOST'] = 'FAKE'
        else:
            # Restore original value
            environ['NERSC_HOST'] = nersc_host
        deps = dependencies(join(self.data_dir, 'nersc_dependencies.txt'))
        self.assertEqual(set(deps),
                         set(['astropy-hpcp', 'setuptools-hpcp',
                              'desiutil/1.0.0']))
        # Clean up the environment.
        if environ['NERSC_HOST'] == 'FAKE':
            del environ['NERSC_HOST']

    def test_get_options(self):
        """Test the processing of desiInstall command-line arguments.
        """
        # Set a few environment variables for testing purposes.
        env_settings = {
            'MODULESHOME': {'old': None, 'new': '/fake/module/directory'},
            'DESI_PRODUCT_ROOT': {'old': None, 'new': '/fake/desi/directory'},
            }
        for key in env_settings:
            if key in environ:
                env_settings[key]['old'] = environ[key]
            environ[key] = env_settings[key]['new']
        default_namespace = Namespace(
            anaconda=self.desiInstall.anaconda_version(),
            bootstrap=False,
            config_file='',
            cross_install=False,
            default=False,
            force=False,
            force_build_type=False,
            keep=False,
            moduledir=u'',
            moduleshome='/fake/module/directory',
            product=u'NO PACKAGE',
            product_version=u'NO VERSION',
            root='/fake/desi/directory',
            test=False,
            username=environ['USER'],
            verbose=False)
        options = self.desiInstall.get_options([])
        self.assertEqual(options, default_namespace)
        default_namespace.product = 'product'
        default_namespace.product_version = 'version'
        options = self.desiInstall.get_options(['product', 'version'])
        self.assertEqual(options, default_namespace)
        default_namespace.default = True
        options = self.desiInstall.get_options(['-d', 'product', 'version'])
        self.assertEqual(options, default_namespace)
        #
        # Examine the log.
        #
        default_namespace.default = False
        default_namespace.verbose = True
        options = self.desiInstall.get_options(['-v', 'product', 'version'])
        self.assertTrue(self.desiInstall.options.verbose)
        self.assertLog(order=-1, message="Set log level to DEBUG.")
        self.assertLog(order=-2,
                       message="Called parse_args() with: -v product version")
        # Test missing environment:
        del environ['DESI_PRODUCT_ROOT']
        options = self.desiInstall.get_options(['-v', 'product', 'version'])
        default_namespace.root = None
        self.assertEqual(options, default_namespace)
        # Restore environment.
        for key in env_settings:
            if env_settings[key]['old'] is None:
                try:
                    del environ[key]
                except KeyError:
                    # Catch double-del.
                    pass
            else:
                environ[key] = env_settings[key]['old']

    def test_sanity_check(self):
        """Test the validation of command-line options.
        """
        options = self.desiInstall.get_options([])
        with self.assertRaises(DesiInstallException) as cm:
            self.desiInstall.sanity_check()
        self.assertEqual(str(cm.exception),
                         "You must specify a product and a version!")
        if 'MODULESHOME' in environ:
            original_mh = environ['MODULESHOME']
        else:
            original_mh = None
        environ['MODULESHOME'] = self.data_dir
        options = self.desiInstall.get_options(['-b'])
        self.desiInstall.sanity_check()
        self.assertTrue(options.bootstrap)
        self.assertEqual(options.product, 'desiutil')
        #
        del environ['MODULESHOME']
        options = self.desiInstall.get_options(['-b'])
        with self.assertRaises(DesiInstallException) as cm:
            self.desiInstall.sanity_check()
        self.assertEqual(str(cm.exception),
                         "You do not appear to have Modules set up.")
        if original_mh is not None:
            environ['MODULESHOME'] = original_mh

    def test_get_product_version(self):
        """Test resolution of product/version input.
        """
        ini = 'desiInstall_configuration.ini'
        options = self.desiInstall.get_options(['foo', 'bar'])
        out = self.desiInstall.get_product_version()
        self.assertEqual(out, (u'https://github.com/desihub/foo',
                         'foo', 'bar'))
        options = self.desiInstall.get_options(['desiutil', '1.0.0'])
        out = self.desiInstall.get_product_version()
        self.assertEqual(out, (u'https://github.com/desihub/desiutil',
                         'desiutil', '1.0.0'))
        options = self.desiInstall.get_options(['desihub/desispec', '2.0.0'])
        out = self.desiInstall.get_product_version()
        self.assertEqual(out, (u'https://github.com/desihub/desispec',
                         'desispec', '2.0.0'))
        options = self.desiInstall.get_options(['--configuration',
                                                join(self.data_dir, ini),
                                                'my_new_product', '1.2.3'])
        out = self.desiInstall.get_product_version()
        self.assertEqual(out, (u'https://github.com/me/my_new_product',
                         'my_new_product', '1.2.3'))
        # Reset the config attribute after testing.
        self.desiInstall.config = None

    def test_identify_branch(self):
        """Test identification of branch installs.
        """
        options = self.desiInstall.get_options(['desiutil', '1.0.0'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         ('https://github.com/desihub/desiutil/archive/' +
                          '1.0.0.tar.gz'))
        options = self.desiInstall.get_options(['desiutil', 'master'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         'https://github.com/desihub/desiutil.git')
        options = self.desiInstall.get_options(['desiAdmin', '1.0.0'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         ('https://desi.lbl.gov/svn/code/tools/desiAdmin/' +
                          'tags/1.0.0'))
        options = self.desiInstall.get_options(['desiAdmin', 'trunk'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         'https://desi.lbl.gov/svn/code/tools/desiAdmin/trunk')
        options = self.desiInstall.get_options(['desiAdmin',
                                                'branches/testing'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         ('https://desi.lbl.gov/svn/code/tools/desiAdmin/' +
                          'branches/testing'))

    def test_verify_url(self):
        """Test the check for a valid svn URL.
        """
        options = self.desiInstall.get_options(['-v', 'desispec', '0.1'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertTrue(self.desiInstall.verify_url())
        self.desiInstall.product_url = 'http://desi.lbl.gov/no/such/place'
        with self.assertRaises(DesiInstallException) as cm:
            self.desiInstall.verify_url()
        message = ("Error {0:d} querying GitHub URL: {1}.".format(
                   404, self.desiInstall.product_url))
        self.assertEqual(str(cm.exception), message)
        options = self.desiInstall.get_options(['-v', 'desiAdmin', 'trunk'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.desiInstall.verify_url(svn='echo')
        message = ' '.join(['--non-interactive', '--username',
                           self.desiInstall.options.username,
                           'ls', self.desiInstall.product_url]) + "\n"
        self.assertLog(-1, message=message)
        with self.assertRaises(DesiInstallException):
            self.desiInstall.verify_url(svn='which')

    def test_build_type(self):
        """Test the determination of the build type.
        """
        options = self.desiInstall.get_options([])
        if hasattr(self.desiInstall, 'working_dir'):
            old_working_dir = self.desiInstall.working_dir
        else:
            old_working_dir = None
        self.desiInstall.working_dir = self.data_dir
        self.assertEqual(self.desiInstall.working_dir, self.data_dir)
        options = self.desiInstall.get_options(['desispec', '1.0.0'])
        self.assertEqual(self.desiInstall.build_type, set(['plain']))
        options = self.desiInstall.get_options(['-C', 'desispec', '1.0.0'])
        self.assertEqual(self.desiInstall.build_type, set(['plain', 'make']))
        # Create temporary files
        options = self.desiInstall.get_options(['desispec', '1.0.0'])
        tempfiles = {'Makefile': 'make', 'setup.py': 'py'}
        for t in tempfiles:
            tempfile = join(self.data_dir, t)
            with open(tempfile, 'w') as tf:
                tf.write('Temporary file.\n')
            self.assertEqual(self.desiInstall.build_type,
                             set(['plain', tempfiles[t]]))
            remove(tempfile)
        # Create temporary directories
        tempdirs = {'src': 'src'}
        for t in tempdirs:
            tempdir = join(self.data_dir, t)
            mkdir(tempdir)
            self.assertEqual(self.desiInstall.build_type,
                             set(['plain', tempdirs[t]]))
            rmdir(tempdir)
        if old_working_dir is None:
            del self.desiInstall.working_dir
        else:
            self.desiInstall.working_dir = old_working_dir

    def test_anaconda_version(self):
        """Test determination of the DESI+Anaconda version.
        """
        try:
            old_desiconda = environ['DESICONDA']
            del environ['DESICONDA']
        except KeyError:
            old_desiconda = None
        v = self.desiInstall.anaconda_version()
        self.assertEqual(v, 'current')
        environ['DESICONDA'] = '/global/common/cori/contrib/desi/desiconda/20170613-1.1.4-spectro/code/desiconda/20170613-1.1.4-spectro_conda'
        v = self.desiInstall.anaconda_version()
        self.assertEqual(v, '20170613-1.1.4-spectro')
        environ['DESICONDA'] = '/global/common/cori/contrib/desi/desiconda/20170613-1.1.4-spectro/CODE/desiconda/20170613-1.1.4-spectro_conda'
        v = self.desiInstall.anaconda_version()
        self.assertEqual(v, 'current')
        if old_desiconda is None:
            del environ['DESICONDA']
        else:
            environ['DESICONDA'] = old_desiconda

    def test_default_nersc_dir(self):
        """Test determination of the NERSC installation root.
        """
        options = self.desiInstall.get_options(['desiutil', 'master'])
        self.desiInstall.nersc = 'edison'
        nersc_dir = self.desiInstall.default_nersc_dir()
        edison_nersc_dir = '/global/common/edison/contrib/desi/desiconda/current'
        if 'DESICONDA' in environ:
            edison_nersc_dir = edison_nersc_dir.replace('current', self.desiInstall.anaconda_version())
        self.assertEqual(nersc_dir, edison_nersc_dir)
        options = self.desiInstall.get_options(['--anaconda',
                                                'frobulate',
                                                'desiutil', 'master'])
        self.desiInstall.nersc = 'datatran'
        nersc_dir = self.desiInstall.default_nersc_dir()
        self.assertEqual(nersc_dir, '/global/project/projectdirs/desi/software/datatran/desiconda/frobulate')

    def test_set_install_dir(self):
        """Test the determination of the install directory.
        """
        try:
            old_nersc_host = environ['NERSC_HOST']
            del environ['NERSC_HOST']
        except KeyError:
            old_nersc_host = None
        options = self.desiInstall.get_options(['--root',
                                                '/fake/root/directory',
                                                'desiutil', 'master'])
        with self.assertRaises(DesiInstallException):
            install_dir = self.desiInstall.set_install_dir()
        options = self.desiInstall.get_options(['--root', self.data_dir,
                                                'desiutil', 'master'])
        self.desiInstall.get_product_version()
        install_dir = self.desiInstall.set_install_dir()
        self.assertEqual(install_dir, join(self.data_dir, 'code', 'desiutil',
                         'master'))
        # Test for presence of existing directory.
        tmpdir = join(self.data_dir, 'code')
        mkdir(tmpdir)
        mkdir(join(tmpdir, 'desiutil'))
        mkdir(join(tmpdir, 'desiutil', 'master'))
        options = self.desiInstall.get_options(['--root', self.data_dir,
                                                'desiutil', 'master'])
        self.desiInstall.get_product_version()
        with self.assertRaises(DesiInstallException) as cm:
            install_dir = self.desiInstall.set_install_dir()
        self.assertEqual(str(cm.exception),
                         "Install directory, {0}, already exists!".format(
                         join(tmpdir, 'desiutil', 'master')))
        options = self.desiInstall.get_options(['--root', self.data_dir,
                                                '--force', 'desiutil',
                                                'master'])
        self.assertTrue(self.desiInstall.options.force)
        self.desiInstall.get_product_version()
        install_dir = self.desiInstall.set_install_dir()
        self.assertFalse(isdir(join(tmpdir, 'desiutil', 'master')))
        if isdir(tmpdir):
            rmtree(tmpdir)
        # Test NERSC installs.  Unset DESI_PRODUCT_ROOT for this to work.
        try:
            old_root = environ['DESI_PRODUCT_ROOT']
            del environ['DESI_PRODUCT_ROOT']
        except KeyError:
            old_root = None
        environ['NERSC_HOST'] = 'edison'
        test_code_version = 'test-blat-foo'
        options = self.desiInstall.get_options(['desiutil', test_code_version])
        self.desiInstall.get_product_version()
        install_dir = self.desiInstall.set_install_dir()
        self.assertEqual(install_dir, join(
                         self.desiInstall.default_nersc_dir(), 'code',
                         'desiutil', test_code_version))
        if old_root is not None:
            environ['DESI_PRODUCT_ROOT'] = old_root
        if old_nersc_host is None:
            del environ['NERSC_HOST']
        else:
            environ['NERSC_HOST'] = old_nersc_host

    @unittest.skipUnless('MODULESHOME' in environ,
                         'Skipping because MODULESHOME is not defined.')
    def test_start_modules(self):
        """Test the initialization of the Modules environment.
        """
        options = self.desiInstall.get_options(['-m',
                                                '/fake/modules/directory',
                                                'desiutil', 'master'])
        with self.assertRaises(DesiInstallException) as cm:
            status = self.desiInstall.start_modules()
        self.assertEqual(str(cm.exception), ("Could not initialize Modules " +
                         "with MODULESHOME={0}!").format(
                         '/fake/modules/directory'))
        options = self.desiInstall.get_options(['desiutil', 'master'])
        status = self.desiInstall.start_modules()
        self.assertTrue(callable(self.desiInstall.module))

    def test_nersc_module_dir(self):
        """Test the nersc_module_dir property.
        """
        ini = 'desiInstall_configuration.ini'
        self.assertIsNone(self.desiInstall.nersc_module_dir)
        self.desiInstall.nersc = None
        self.assertIsNone(self.desiInstall.nersc_module_dir)
        options = self.desiInstall.get_options(['desiutil', '1.9.5'])
        for n in ('edison', 'cori', 'datatran', 'scigate'):
            self.desiInstall.nersc = n
            self.desiInstall.baseproduct = 'desiutil'
            self.assertEqual(self.desiInstall.nersc_module_dir,
                             join(self.desiInstall.default_nersc_dir(n),
                                  "modulefiles"))
            self.desiInstall.baseproduct = 'desimodules'
            self.assertEqual(self.desiInstall.nersc_module_dir,
                             join(self.desiInstall.default_nersc_dir_templates[n].format(desiconda_version='startup'),
                                  "modulefiles"))
        options = self.desiInstall.get_options(['--configuration',
                                                join(self.data_dir, ini),
                                                'my_new_product', '1.2.3'])
        self.desiInstall.nersc = 'edison'
        self.assertEqual(self.desiInstall.nersc_module_dir,
                         '/project/projectdirs/desi/test/modules')
        self.desiInstall.nersc = 'cori'
        self.assertEqual(self.desiInstall.nersc_module_dir,
                         '/global/common/cori/contrib/desi/test/modules')

    def test_cleanup(self):
        """Test the cleanup stage of the install.
        """
        options = self.desiInstall.get_options(['desiutil', 'master'])
        self.desiInstall.original_dir = getcwd()
        self.desiInstall.working_dir = join(self.data_dir, 'desiutil-master')
        mkdir(self.desiInstall.working_dir)
        chdir(self.desiInstall.working_dir)
        self.desiInstall.cleanup()
        self.assertEqual(getcwd(), self.desiInstall.original_dir)
        self.assertFalse(isdir(self.desiInstall.working_dir))


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
