# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.install.
"""
import sys
import unittest
from unittest.mock import patch, call, MagicMock, mock_open
from os import chdir, environ, getcwd, mkdir, remove, rmdir
from os.path import abspath, basename, isdir, join
from shutil import rmtree
from argparse import Namespace
from tempfile import mkdtemp
from logging import getLogger
from importlib.resources import files
from ..log import DEBUG
from ..install import DesiInstall, DesiInstallException, dependencies
from .test_log import NullMemoryHandler


def replace_stat(filename):
    """Mock os.stat().
    """
    class st_mode(object):
        def __init__(self, st_mode):
            self.st_mode = st_mode

    if basename(filename) == 'executable':
        return st_mode(33133)
    return st_mode(33184)


class TestInstall(unittest.TestCase):
    """Test desiutil.install.
    """

    @classmethod
    def setUpClass(cls):
        cls.py = f"python{sys.version_info.major:d}.{sys.version_info.minor:d}"
        cls.cext = f"cpython-{sys.version_info.major:d}.{sys.version_info.minor:d}.pyc"

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        # Create a "fresh" DesiInstall object for every test.
        self.desiInstall = DesiInstall()
        # Replace the log handler with something that writes to memory.
        root_logger = getLogger(self.desiInstall.log.name.rsplit('.', 1)[0])
        while len(root_logger.handlers) > 0:
            h = root_logger.handlers[0]
            fmt = h.formatter
            root_logger.removeHandler(h)
        mh = NullMemoryHandler()
        mh.setFormatter(fmt)
        root_logger.addHandler(mh)
        self.desiInstall.log.setLevel(DEBUG)
        # Create a temporary directory.
        self.data_dir = mkdtemp()

    def tearDown(self):
        rmtree(self.data_dir)

    def assertLog(self, order=-1, message=''):
        """Examine the log messages.
        """
        handler = getLogger(self.desiInstall.log.name.rsplit('.', 1)[0]).handlers[0]
        record = handler.buffer[order]
        self.assertEqual(record.getMessage(), message)

    def test_dependencies(self):
        """Test dependency processing.
        """
        # Raise ValueError if file doesn't exist:
        with self.assertRaises(ValueError) as cm:
            dependencies("foo/bar/baz.module")
        self.assertEqual(str(cm.exception),
                         "Modulefile foo/bar/baz.module does not exist!")
        # Standard dependencies.
        deps = dependencies(str(files('desiutil.test') / 't' / 'generic_dependencies.txt'))
        self.assertEqual(set(deps), set(['astropy', 'desiutil/1.0.0']))

    def test_get_options(self):
        """Test the processing of desiInstall command-line arguments.
        """
        # Set a few environment variables for testing purposes.
        with patch.dict('os.environ', {'MODULESHOME': '/fake/module/directory'}):
            default_namespace = Namespace(
                additional=None,
                anaconda=self.desiInstall.anaconda_version(),
                bootstrap=False,
                default=False,
                force=False,
                force_build_type=False,
                keep=False,
                moduleshome='/fake/module/directory',
                product=u'NO PACKAGE',
                product_version=u'NO VERSION',
                root=None,
                test=False,
                username=environ['USER'],
                verbose=False,
                world=True)
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

    def test_sanity_check(self):
        """Test the validation of command-line options.
        """
        options = self.desiInstall.get_options([])
        with self.assertRaises(DesiInstallException) as cm:
            self.desiInstall.sanity_check()
        self.assertEqual(str(cm.exception),
                         "You must specify a product and a version!")
        with patch.dict('os.environ', {'MODULESHOME': self.data_dir}):
            options = self.desiInstall.get_options(['-b'])
            self.desiInstall.sanity_check()
            self.assertTrue(options.bootstrap)
            self.assertEqual(options.product, 'desiutil')
            del environ['MODULESHOME']
            options = self.desiInstall.get_options(['-b'])
            with self.assertRaises(DesiInstallException) as cm:
                self.desiInstall.sanity_check()
            self.assertEqual(str(cm.exception),
                             "You do not appear to have Modules set up.")

    def test_get_product_version(self):
        """Test resolution of product/version input.
        """
        with patch.dict('desiutil.install.known_products',
                        {'desiutil': 'https://github.com/desihub/desiutil',
                         'desispec': 'https://github.com/desihub/desispec'}):
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
            options = self.desiInstall.get_options(['-p',
                                                    'my_new_product:https://github.com/me/my_new_product',
                                                    'my_new_product',
                                                    '1.2.3'])
            out = self.desiInstall.get_product_version()
            self.assertEqual(out, (u'https://github.com/me/my_new_product',
                                   'my_new_product', '1.2.3'))
            options = self.desiInstall.get_options(['-p',
                                                    'desiutil:https://github.com/me/desiutil',
                                                    'desiutil',
                                                    '1.2.3'])
            out = self.desiInstall.get_product_version()
            self.assertEqual(out, (u'https://github.com/me/desiutil',
                                   'desiutil', '1.2.3'))

    def test_identify_branch(self):
        """Test identification of branch installs.
        """
        options = self.desiInstall.get_options(['desiutil', '1.0.0'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         ('https://github.com/desihub/desiutil/archive/' +
                          '1.0.0.tar.gz'))
        options = self.desiInstall.get_options(['desiutil', 'branches/main'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         'https://github.com/desihub/desiutil.git')
        options = self.desiInstall.get_options(['plate_layout', '1.0.0'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         ('https://desi.lbl.gov/svn/code/focalplane/plate_layout/' +
                          'tags/1.0.0'))
        options = self.desiInstall.get_options(['plate_layout', 'trunk'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         'https://desi.lbl.gov/svn/code/focalplane/plate_layout/trunk')
        options = self.desiInstall.get_options(['plate_layout', 'branches/trunk'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         'https://desi.lbl.gov/svn/code/focalplane/plate_layout/trunk')
        options = self.desiInstall.get_options(['plate_layout',
                                                'branches/testing'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertEqual(url,
                         ('https://desi.lbl.gov/svn/code/focalplane/plate_layout/' +
                          'branches/testing'))

    def test_verify_url(self):
        """Test the check for a valid svn URL.
        """
        options = self.desiInstall.get_options(['-v', 'desispec', '0.1'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.assertTrue(self.desiInstall.verify_url())
        self.desiInstall.product_url = 'https://desi.lbl.gov/no/such/place'
        with self.assertRaises(DesiInstallException) as cm:
            self.desiInstall.verify_url()
        message = ("Error {0:d} querying GitHub URL: {1}.".format(
                   404, self.desiInstall.product_url))
        self.assertEqual(str(cm.exception), message)
        options = self.desiInstall.get_options(['-v', 'plate_layout', 'trunk'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        self.desiInstall.verify_url(svn='echo')
        message = ' '.join(['--non-interactive', '--username',
                           self.desiInstall.options.username,
                           'ls', self.desiInstall.product_url]) + "\n"
        self.assertLog(-1, message=message)
        with self.assertRaises(DesiInstallException):
            self.desiInstall.verify_url(svn='which')

    @patch('desiutil.install.Popen')
    @patch('shutil.rmtree')
    @patch('os.path.isdir')
    def test_get_code_svn_export(self, mock_isdir, mock_rmtree, mock_popen):
        """Test downloads via svn export.
        """
        options = self.desiInstall.get_options(['-v', 'plate_layout', '0.1'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        mock_isdir.return_value = True
        mock_proc = mock_popen()
        mock_proc.communicate.return_value = ('out', '')
        mock_proc.returncode = 0
        self.desiInstall.get_code()
        self.assertEqual(self.desiInstall.working_dir, join(abspath('.'), 'plate_layout-0.1'))
        mock_isdir.assert_called_once_with(self.desiInstall.working_dir)
        mock_rmtree.assert_called_once_with(self.desiInstall.working_dir)
        mock_popen.assert_has_calls([call(['svn', '--non-interactive', '--username',
                                           self.desiInstall.options.username, 'export',
                                           'https://desi.lbl.gov/svn/code/focalplane/plate_layout/tags/0.1',
                                           self.desiInstall.working_dir], universal_newlines=True, stdout=-1, stderr=-1),
                                     call().communicate()])

    @patch('desiutil.install.Popen')
    @patch('os.path.isdir')
    def test_get_code_svn_branch(self, mock_isdir, mock_popen):
        """Test downloads via svn checkout.
        """
        options = self.desiInstall.get_options(['-v', 'plate_layout', 'branches/test'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        mock_isdir.return_value = False
        mock_proc = mock_popen()
        mock_proc.communicate.return_value = ('out', '')
        mock_proc.returncode = 0
        self.desiInstall.get_code()
        self.assertEqual(self.desiInstall.working_dir, join(abspath('.'), 'plate_layout-test'))
        mock_isdir.assert_called_once_with(self.desiInstall.working_dir)
        mock_popen.assert_has_calls([call(['svn', '--non-interactive', '--username',
                                           self.desiInstall.options.username, 'checkout',
                                           'https://desi.lbl.gov/svn/code/focalplane/plate_layout/branches/test',
                                           self.desiInstall.working_dir], universal_newlines=True, stdout=-1, stderr=-1),
                                     call().communicate()])

    @patch('desiutil.install.Popen')
    @patch('os.path.isdir')
    def test_get_code_svn_error(self, mock_isdir, mock_popen):
        """Test downloads via svn checkout with error handling.
        """
        options = self.desiInstall.get_options(['-v', 'plate_layout', '0.1'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        mock_isdir.return_value = False
        mock_proc = mock_popen()
        mock_proc.communicate.return_value = ('out', 'err')
        mock_proc.returncode = 1
        with self.assertRaises(DesiInstallException) as cm:
            self.desiInstall.get_code()
        self.assertEqual(self.desiInstall.working_dir, join(abspath('.'), 'plate_layout-0.1'))
        mock_isdir.assert_called_once_with(self.desiInstall.working_dir)
        mock_popen.assert_has_calls([call(['svn', '--non-interactive', '--username',
                                           self.desiInstall.options.username, 'export',
                                           'https://desi.lbl.gov/svn/code/focalplane/plate_layout/tags/0.1',
                                           self.desiInstall.working_dir], universal_newlines=True, stdout=-1, stderr=-1).
                                     call().communicate()])
        message = "svn error while downloading product code: err"
        self.assertLog(-1, message)
        self.assertEqual(str(cm.exception), message)

    @patch('os.path.isdir')
    def test_get_code_svn_test(self, mock_isdir):
        """Test downloads via svn checkout in test mode.
        """
        options = self.desiInstall.get_options(['-t', 'plate_layout', '0.1'])
        out = self.desiInstall.get_product_version()
        url = self.desiInstall.identify_branch()
        mock_isdir.return_value = False
        self.desiInstall.get_code()
        self.assertEqual(self.desiInstall.working_dir, join(abspath('.'), 'plate_layout-0.1'))
        mock_isdir.assert_called_once_with(self.desiInstall.working_dir)
        self.assertLog(-1, 'Test Mode.')

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
        tempfiles = {'Makefile': 'make', 'pyproject.toml': 'py', 'setup.py': 'py'}
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
        with patch.dict('os.environ', {'DESICONDA': 'FOO'}):
            v = self.desiInstall.anaconda_version()
            self.assertEqual(v, 'current')
            environ['DESICONDA'] = '/global/common/software/desi/cori/desiconda/20170613-1.1.4-spectro/conda'
            v = self.desiInstall.anaconda_version()
            self.assertEqual(v, '20170613-1.1.4-spectro')
            environ['DESICONDA'] = '/global/common/software/desi/cori/desiconda/20170613-1.1.4-spectro/code/desiconda/20170613-1.1.4-spectro_conda'
            v = self.desiInstall.anaconda_version()
            self.assertEqual(v, 'current')

    def test_default_nersc_dir(self):
        """Test determination of the NERSC installation root.
        """
        options = self.desiInstall.get_options(['desiutil', 'branches/main'])
        self.desiInstall.nersc = 'edison'
        nersc_dir = self.desiInstall.default_nersc_dir()
        edison_nersc_dir = '/global/common/software/desi/edison/desiconda/current'
        if 'DESICONDA' in environ:
            edison_nersc_dir = edison_nersc_dir.replace('current', self.desiInstall.anaconda_version())
        self.assertEqual(nersc_dir, edison_nersc_dir)
        options = self.desiInstall.get_options(['--anaconda',
                                                'frobulate',
                                                'desiutil', '1.2.3'])
        self.desiInstall.nersc = 'datatran'
        nersc_dir = self.desiInstall.default_nersc_dir()
        self.assertEqual(nersc_dir, '/global/common/software/desi/datatran/desiconda/frobulate')

    def test_set_install_dir(self):
        """Test the determination of the install directory.
        """
        with patch.dict('os.environ', {'NERSC_HOST': 'FAKE'}):
            del environ['NERSC_HOST']
            options = self.desiInstall.get_options(['--root',
                                                    '/fake/root/directory',
                                                    'desiutil', '1.2.3'])
            with self.assertRaises(DesiInstallException):
                install_dir = self.desiInstall.set_install_dir()
            options = self.desiInstall.get_options(['--root', self.data_dir,
                                                    'desiutil', '1.2.3'])
            self.desiInstall.get_product_version()
            install_dir = self.desiInstall.set_install_dir()
            self.assertEqual(install_dir, join(self.data_dir, 'code', 'desiutil',
                             '1.2.3'))
            # Test for presence of existing directory.
            tmpdir = join(self.data_dir, 'code')
            mkdir(tmpdir)
            mkdir(join(tmpdir, 'desiutil'))
            mkdir(join(tmpdir, 'desiutil', 'main'))
            options = self.desiInstall.get_options(['--root', self.data_dir,
                                                    'desiutil', 'branches/main'])
            self.desiInstall.get_product_version()
            with self.assertRaises(DesiInstallException) as cm:
                install_dir = self.desiInstall.set_install_dir()
            self.assertEqual(str(cm.exception),
                             "Install directory, {0}, already exists!".format(
                             join(tmpdir, 'desiutil', 'main')))
            options = self.desiInstall.get_options(['--root', self.data_dir,
                                                    '--force', 'desiutil',
                                                    'branches/main'])
            self.assertTrue(self.desiInstall.options.force)
            self.desiInstall.get_product_version()
            install_dir = self.desiInstall.set_install_dir()
            self.assertFalse(isdir(join(tmpdir, 'desiutil', 'branches/main')))
            if isdir(tmpdir):
                rmtree(tmpdir)
        # Test NERSC installs.  Unset DESI_PRODUCT_ROOT for this to work.
        with patch.dict('os.environ', {'NERSC_HOST': 'edison', 'DESI_PRODUCT_ROOT': 'FAKE'}):
            del environ['DESI_PRODUCT_ROOT']
            test_code_version = 'test-blat-foo'
            options = self.desiInstall.get_options(['desiutil', test_code_version, '--test'])
            self.desiInstall.get_product_version()
            install_dir = self.desiInstall.set_install_dir()
            self.assertEqual(install_dir, join(
                             self.desiInstall.default_nersc_dir(), 'code',
                             'desiutil', test_code_version))

    @unittest.skipUnless('MODULESHOME' in environ,
                         'Skipping because MODULESHOME is not defined.')
    def test_start_modules(self):
        """Test the initialization of the Modules environment.
        """
        options = self.desiInstall.get_options(['-m',
                                                '/fake/modules/directory',
                                                'desiutil', 'branches/main'])
        with self.assertRaises(DesiInstallException) as cm:
            status = self.desiInstall.start_modules()
        self.assertEqual(str(cm.exception), ("Could not initialize Modules " +
                         "with MODULESHOME={0}!").format(
                         '/fake/modules/directory'))
        options = self.desiInstall.get_options(['desiutil', 'branches/main'])
        self.assertEqual(options.moduleshome, environ['MODULESHOME'])
        status = self.desiInstall.start_modules()
        self.assertTrue(callable(self.desiInstall.module))

    @patch('desiutil.install.dependencies')
    @patch('os.path.exists')
    def test_module_dependencies(self, mock_exists, mock_dependencies):
        """Test module-loading dependencies.
        """
        mock_dependencies.return_value = ['desiutil/main', 'foobar']
        mock_exists.return_value = True
        options = self.desiInstall.get_options(['desispec', '1.9.5'])
        self.desiInstall.baseproduct = 'desispec'
        self.desiInstall.working_dir = join(self.data_dir, 'desispec')
        self.desiInstall.module = MagicMock()
        self.assertFalse(self.desiInstall.options.test)
        with patch.dict('os.environ', {'LOADEDMODULES': 'desiutil'}):
            deps = self.desiInstall.module_dependencies()
        self.assertListEqual(self.desiInstall.deps, ['desiutil/main', 'foobar'])
        self.assertEqual(self.desiInstall.module_file, join(self.desiInstall.working_dir, 'etc', 'desispec.module'))
        self.desiInstall.module.assert_has_calls([call('switch', 'desiutil/main'), call('load', 'foobar')])
        mock_exists.assert_has_calls([call(join(self.desiInstall.working_dir, 'etc', 'desispec.module'))], any_order=True)
        mock_dependencies.assert_called_once_with(join(self.desiInstall.working_dir, 'etc', 'desispec.module'))

    def test_module_dependencies_test_mode(self):
        """Test module-loading dependencies in test mode.
        """
        options = self.desiInstall.get_options(['--test', 'desutil', '1.9.5'])
        self.desiInstall.baseproduct = 'desiutil'
        self.desiInstall.working_dir = join(self.data_dir, 'desiutil')
        self.assertTrue(self.desiInstall.options.test)
        deps = self.desiInstall.module_dependencies()
        self.assertListEqual(self.desiInstall.deps, [])
        self.assertLog(-1, 'Test Mode. Skipping loading of dependencies.')

    def test_nersc_module_dir(self):
        """Test the nersc_module_dir property.
        """
        self.assertIsNone(self.desiInstall.nersc_module_dir)
        self.desiInstall.nersc = None
        self.assertIsNone(self.desiInstall.nersc_module_dir)
        test_args = ['--anaconda', '20180102-1.2.3-spec', 'desiutil', '1.9.5']
        options = self.desiInstall.get_options(test_args)
        for n in ('edison', 'cori', 'datatran', 'scigate'):
            self.desiInstall.nersc = n
            self.desiInstall.baseproduct = 'desiutil'
            self.assertEqual(self.desiInstall.nersc_module_dir,
                             join(self.desiInstall.default_nersc_dir(n),
                                  "modulefiles"))
        options = self.desiInstall.get_options(['--root', '/global/cfs/cdirs/desi/test',
                                                'desiutil', '1.9.5'])
        self.assertEqual(self.desiInstall.nersc_module_dir,
                         '/global/cfs/cdirs/desi/test/modulefiles')

    def test_install_module(self):
        """Test installation of module files.
        """
        pass

    def test_prepare_environment(self):
        """Test set up of build environment.
        """
        pass

    def test_install(self):
        """Test the actuall installation process.
        """
        pass

    @patch('os.path.exists')
    @patch('desiutil.install.Popen')
    def test_get_extra(self, mock_popen, mock_exists):
        """Test fetching extra data.
        """
        options = self.desiInstall.get_options(['desiutil', 'branches/main'])
        self.desiInstall.baseproduct = 'desiutil'
        self.desiInstall.working_dir = join(self.data_dir, 'desiutil')
        mock_exists.return_value = True
        mock_proc = mock_popen()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = ('out', 'err')
        self.desiInstall.get_extra()
        mock_popen.assert_has_calls([call([join(self.desiInstall.working_dir, 'etc', 'desiutil_data.sh')], stderr=-1, stdout=-1, universal_newlines=True)],
                                    any_order=True)
        mock_popen.reset_mock()
        self.desiInstall.options.test = True
        self.desiInstall.get_extra()
        self.assertLog(-1, 'Test Mode. Skipping install of extra data.')
        mock_popen.reset_mock()
        self.desiInstall.options.test = False
        mock_proc = mock_popen()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = ('out', 'err')
        with self.assertRaises(DesiInstallException) as cm:
            self.desiInstall.get_extra()
        message = "Error grabbing extra data: err"
        self.assertLog(-1, message)
        self.assertEqual(str(cm.exception), message)

    @patch('os.chdir')
    @patch('os.path.exists')
    @patch('desiutil.install.Popen')
    def test_compile_branch(self, mock_popen, mock_exists, mock_chdir):
        """Test compiling code in certain cases.
        """
        current_dir = getcwd()
        options = self.desiInstall.get_options(['fiberassign', 'branches/main'])
        self.desiInstall.baseproduct = 'fiberassign'
        self.desiInstall.is_branch = True
        self.desiInstall.install_dir = join(self.data_dir, 'fiberassign')
        mock_exists.return_value = True
        mock_proc = mock_popen()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = ('out', 'err')
        self.desiInstall.compile_branch()
        mock_chdir.assert_has_calls([call(self.desiInstall.install_dir),
                                     call(current_dir)])
        mock_exists.assert_has_calls([call(join(self.desiInstall.install_dir, 'etc', 'fiberassign_compile.sh'))])
        mock_popen.assert_has_calls([call([join(self.desiInstall.install_dir, 'etc', 'fiberassign_compile.sh'), sys.executable],
                                          stderr=-1, stdout=-1, universal_newlines=True)], any_order=True)
        mock_popen.reset_mock()
        self.desiInstall.options.test = True
        self.desiInstall.compile_branch()
        self.assertLog(-1, 'Test Mode. Skipping compile script.')
        mock_popen.reset_mock()
        self.desiInstall.options.test = False
        mock_proc = mock_popen()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = ('out', 'err')
        with self.assertRaises(DesiInstallException) as cm:
            self.desiInstall.compile_branch()
        message = "Error compiling code: err"
        self.assertLog(-1, message)
        self.assertEqual(str(cm.exception), message)

    def test_verify_bootstrap(self):
        """Test proper installation of the desiInstall executable.
        """
        options = self.desiInstall.get_options(['-b', '-a', '20211217-2.0.0'])
        self.desiInstall.install_dir = join(self.data_dir, 'desiutil')
        data = """#!/global/common/software/desi/cori/desiconda//20211217-2.0.0/conda/bin/python
# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst
from sys import exit
from desiutil.install import main
exit(main())
"""
        with patch('builtins.open', mock_open(read_data=data)) as m:
            self.assertTrue(self.desiInstall.verify_bootstrap())
        m.assert_called_once_with(join(self.desiInstall.install_dir, 'bin', 'desiInstall'), 'r')
        data = """#!/global/common/software/desi/cori/desiconda/current/conda/bin/python
# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst
from sys import exit
from desiutil.install import main
exit(main())
"""
        with patch('builtins.open', mock_open(read_data=data)) as m:
            with self.assertRaises(DesiInstallException) as cm:
                self.desiInstall.verify_bootstrap()
        message = ("desiInstall executable ({0}) does not contain " +
                   "an explicit desiconda version ({1})!").format(join(self.desiInstall.install_dir, 'bin', 'desiInstall'), '20211217-2.0.0')
        self.assertEqual(str(cm.exception), message)
        self.assertLog(-1, message)

    @patch('os.stat', replace_stat)
    @patch('os.walk')
    @patch('os.chmod')
    def test_permissions(self, mock_chmod, mock_walk):
        """Test the permission stage of the install.
        """
        options = self.desiInstall.get_options(['desiutil', '1.2.3'])
        self.assertTrue(self.desiInstall.options.world)
        self.desiInstall.install_dir = join(self.data_dir, 'desiutil')
        self.desiInstall.is_branch = False
        mock_walk.return_value = iter([(join(self.desiInstall.install_dir, 'bin'), [], ['executable', 'README.txt']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil-1.2.3.dist-info'), [], ['METADATA', 'LICENSE.rst']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil', '__pycache__'), [], [f"__init__.{self.cext}", f"module.{self.cext}"]),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil'), ['__pycache__'], ['__init__.py', 'module.py']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages'),
                                        ['desiutil-1.2.3.dist-info', 'desiutil'], []),
                                       (join(self.desiInstall.install_dir, 'lib', self.py), ['site-packages'], []),
                                       (join(self.desiInstall.install_dir, 'lib'), [self.py], []),
                                       (self.desiInstall.install_dir, ['bin', 'lib'], [])])
        self.desiInstall.permissions()
        mock_walk.assert_called_once_with(self.desiInstall.install_dir, topdown=False)
        mock_chmod.assert_has_calls([call(join(self.desiInstall.install_dir, 'bin', 'executable'), 0o555),
                                     call(join(self.desiInstall.install_dir, 'bin', 'README.txt'), 0o444),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info', 'METADATA'), 0o444),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info', 'LICENSE.rst'), 0o444),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__', f"__init__.{self.cext}"), 0o444),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__', f"module.{self.cext}"), 0o444),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__init__.py'), 0o444),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', 'module.py'), 0o444),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__'), 0o2555),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info'), 0o2555),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil'), 0o2555),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages'), 0o2555),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py), 0o2555),
                                     call(join(self.desiInstall.install_dir, 'bin'), 0o2555),
                                     call(join(self.desiInstall.install_dir, 'lib'), 0o2555),
                                     call(self.desiInstall.install_dir, 0o2555)])
        self.assertLog(-2, "os.chmod('%s', %s)" % (join(self.desiInstall.install_dir, 'lib'), 0o2555))
        self.assertLog(-1, "os.chmod('%s', %s)" % (self.desiInstall.install_dir, 0o2555))

    @patch('os.stat', replace_stat)
    @patch('os.walk')
    @patch('os.chmod')
    def test_permissions_with_branch(self, mock_chmod, mock_walk):
        """Test the permission stage of the install with a branch.
        """
        options = self.desiInstall.get_options(['desiutil', 'branches/main'])
        self.assertTrue(self.desiInstall.options.world)
        self.desiInstall.install_dir = join(self.data_dir, 'desiutil')
        self.desiInstall.is_branch = True
        mock_walk.return_value = iter([(join(self.desiInstall.install_dir, 'bin'), [], ['executable', 'README.txt']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil-1.2.3.dist-info'), [], ['METADATA', 'LICENSE.rst']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil', '__pycache__'), [], [f"__init__.{self.cext}", f"module.{self.cext}"]),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil'), ['__pycache__'], ['__init__.py', 'module.py']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages'),
                                        ['desiutil-1.2.3.dist-info', 'desiutil'], []),
                                       (join(self.desiInstall.install_dir, 'lib', self.py), ['site-packages'], []),
                                       (join(self.desiInstall.install_dir, 'lib'), [self.py], []),
                                       (self.desiInstall.install_dir, ['bin', 'lib'], [])])
        self.desiInstall.permissions()
        mock_walk.assert_called_once_with(self.desiInstall.install_dir, topdown=False)
        mock_chmod.assert_has_calls([call(join(self.desiInstall.install_dir, 'bin', 'executable'), 0o755),
                                     call(join(self.desiInstall.install_dir, 'bin', 'README.txt'), 0o644),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info', 'METADATA'), 0o644),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info', 'LICENSE.rst'), 0o644),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__', f"__init__.{self.cext}"), 0o644),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__', f"module.{self.cext}"), 0o644),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__init__.py'), 0o644),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', 'module.py'), 0o644),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__'), 0o2755),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info'), 0o2755),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil'), 0o2755),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages'), 0o2755),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py), 0o2755),
                                     call(join(self.desiInstall.install_dir, 'bin'), 0o2755),
                                     call(join(self.desiInstall.install_dir, 'lib'), 0o2755),
                                     call(self.desiInstall.install_dir, 0o2755)])
        self.assertLog(-2, "os.chmod('%s', %s)" % (join(self.desiInstall.install_dir, 'lib'), 0o2755))
        self.assertLog(-1, "os.chmod('%s', %s)" % (self.desiInstall.install_dir, 0o2755))

    @patch('os.stat', replace_stat)
    @patch('os.walk')
    @patch('os.chmod')
    def test_permissions_without_world(self, mock_chmod, mock_walk):
        """Test the permission stage of the install, disabling world-read.
        """
        options = self.desiInstall.get_options(['--no-world', 'desiutil', '1.2.3'])
        self.assertFalse(self.desiInstall.options.world)
        self.desiInstall.install_dir = join(self.data_dir, 'desiutil')
        self.desiInstall.is_branch = False
        mock_walk.return_value = iter([(join(self.desiInstall.install_dir, 'bin'), [], ['executable', 'README.txt']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil-1.2.3.dist-info'), [], ['METADATA', 'LICENSE.rst']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil', '__pycache__'), [], [f"__init__.{self.cext}", f"module.{self.cext}"]),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil'), ['__pycache__'], ['__init__.py', 'module.py']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages'), ['desiutil-1.2.3.dist-info', 'desiutil'], []),
                                       (join(self.desiInstall.install_dir, 'lib', self.py), ['site-packages'], []),
                                       (join(self.desiInstall.install_dir, 'lib'), [self.py], []),
                                       (self.desiInstall.install_dir, ['bin', 'lib'], [])])
        self.desiInstall.permissions()
        mock_walk.assert_called_once_with(self.desiInstall.install_dir, topdown=False)
        mock_chmod.assert_has_calls([call(join(self.desiInstall.install_dir, 'bin', 'executable'), 0o550),
                                     call(join(self.desiInstall.install_dir, 'bin', 'README.txt'), 0o440),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info', 'METADATA'), 0o440),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info', 'LICENSE.rst'), 0o440),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__', f"__init__.{self.cext}"), 0o440),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__', f"module.{self.cext}"), 0o440),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__init__.py'), 0o440),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', 'module.py'), 0o440),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__'), 0o2550),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info'), 0o2550),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil'), 0o2550),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages'), 0o2550),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py), 0o2550),
                                     call(join(self.desiInstall.install_dir, 'bin'), 0o2550),
                                     call(join(self.desiInstall.install_dir, 'lib'), 0o2550),
                                     call(self.desiInstall.install_dir, 0o2550)])
        self.assertLog(-2, "os.chmod('%s', %s)" % (join(self.desiInstall.install_dir, 'lib'), 0o2550))
        self.assertLog(-1, "os.chmod('%s', %s)" % (self.desiInstall.install_dir, 0o2550))

    @patch('os.stat', replace_stat)
    @patch('os.walk')
    @patch('os.chmod')
    def test_permissions_with_branch_without_world(self, mock_chmod, mock_walk):
        """Test the permission stage of the install, on a branch, disabling world-read.
        """
        options = self.desiInstall.get_options(['--no-world', 'desiutil', 'branches/main'])
        self.assertFalse(self.desiInstall.options.world)
        self.desiInstall.install_dir = join(self.data_dir, 'desiutil')
        self.desiInstall.is_branch = True
        mock_walk.return_value = iter([(join(self.desiInstall.install_dir, 'bin'), [], ['executable', 'README.txt']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil-1.2.3.dist-info'), [], ['METADATA', 'LICENSE.rst']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil', '__pycache__'), [], [f"__init__.{self.cext}", f"module.{self.cext}"]),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                             'desiutil'), ['__pycache__'], ['__init__.py', 'module.py']),
                                       (join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages'), ['desiutil-1.2.3.dist-info', 'desiutil'], []),
                                       (join(self.desiInstall.install_dir, 'lib', self.py), ['site-packages'], []),
                                       (join(self.desiInstall.install_dir, 'lib'), [self.py], []),
                                       (self.desiInstall.install_dir, ['bin', 'lib'], [])])
        self.desiInstall.permissions()
        mock_walk.assert_called_once_with(self.desiInstall.install_dir, topdown=False)
        mock_chmod.assert_has_calls([call(join(self.desiInstall.install_dir, 'bin', 'executable'), 0o750),
                                     call(join(self.desiInstall.install_dir, 'bin', 'README.txt'), 0o640),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info', 'METADATA'), 0o640),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info', 'LICENSE.rst'), 0o640),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__', f"__init__.{self.cext}"), 0o640),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__', f"module.{self.cext}"), 0o640),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__init__.py'), 0o640),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', 'module.py'), 0o640),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil', '__pycache__'), 0o2750),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil-1.2.3.dist-info'), 0o2750),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages',
                                               'desiutil'), 0o2750),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py, 'site-packages'), 0o2750),
                                     call(join(self.desiInstall.install_dir, 'lib', self.py), 0o2750),
                                     call(join(self.desiInstall.install_dir, 'bin'), 0o2750),
                                     call(join(self.desiInstall.install_dir, 'lib'), 0o2750),
                                     call(self.desiInstall.install_dir, 0o2750)])
        self.assertLog(-2, "os.chmod('%s', %s)" % (join(self.desiInstall.install_dir, 'lib'), 0o2750))
        self.assertLog(-1, "os.chmod('%s', %s)" % (self.desiInstall.install_dir, 0o2750))

    @patch('desiutil.install.Popen')
    def test_unlock_permissions(self, mock_popen):
        """Test unlocking installed directories to allow their removal.
        """
        options = self.desiInstall.get_options(['desiutil', 'branches/main'])
        self.desiInstall.install_dir = join(self.data_dir, 'desiutil')
        mock_proc = mock_popen()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = ('out', 'err')
        status = self.desiInstall.unlock_permissions()
        self.assertEqual(status, 0)
        mock_popen.assert_has_calls([call(['chmod', '-R', 'u+w', self.desiInstall.install_dir], stderr=-1, stdout=-1, universal_newlines=True)],
                                    any_order=True)

    def test_cleanup(self):
        """Test the cleanup stage of the install.
        """
        options = self.desiInstall.get_options(['desiutil', 'branches/main'])
        self.desiInstall.original_dir = getcwd()
        self.desiInstall.working_dir = join(self.data_dir, 'desiutil')
        mkdir(self.desiInstall.working_dir)
        chdir(self.desiInstall.working_dir)
        self.desiInstall.cleanup()
        self.assertEqual(getcwd(), self.desiInstall.original_dir)
        self.assertFalse(isdir(self.desiInstall.working_dir))
