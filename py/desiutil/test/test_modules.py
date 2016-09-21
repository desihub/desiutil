# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.modules.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
from types import MethodType
from os import environ, mkdir, remove, rmdir
from os.path import dirname, exists, isdir, join
from sys import version_info
from ..modules import (init_modules, configure_module, process_module,
                       default_module)


class TestModules(unittest.TestCase):
    """Test desiutil.modules.
    """

    @classmethod
    def setUpClass(cls):
        # Data directory
        cls.data_dir = join(dirname(__file__), 't')
        cls.orig_env_cache = dict()
        cls.env_cache = dict()
        cls.module_envs = {'MODULESHOME': cls.data_dir,
                           'MODULEPATH': '', 'LOADEDMODULES': ''}
        #
        # Set up a dummy MODULESHOME for all tests.
        #
        for e in cls.module_envs:
            try:
                cls.orig_env_cache[e] = environ[e]
            except KeyError:
                cls.orig_env_cache[e] = None
            environ[e] = cls.module_envs[e]

    @classmethod
    def tearDownClass(cls):
        for e in cls.module_envs:
            if cls.orig_env_cache[e] is None:
                del environ[e]
            else:
                environ[e] = cls.orig_env_cache[e]

    def cache_env(self, envs):
        """Store existing environment variables in a cache and delete them.
        """
        for e in envs:
            if e in environ:
                self.env_cache[e] = environ[e]
                del environ[e]

    def restore_env(self, envs):
        """Restore environment variables to original values.
        """
        for e in envs:
            if e in self.env_cache:
                environ[e] = self.env_cache[e]
                del self.env_cache[e]

    def test_init_modules(self):
        """Test the initialization of the Modules environment.
        """
        #
        # Presence or absence of MODULESHOME.
        #
        self.cache_env(('MODULESHOME',))
        wrapper_function = init_modules()
        self.assertIsNone(wrapper_function)
        self.restore_env(('MODULESHOME',))
        wrapper_function = init_modules('/fake/modules/directory')
        self.assertIsNone(wrapper_function)
        #
        # Initialies MODULEPATH.
        #
        self.cache_env(('MODULEPATH', 'LOADEDMODULES'))
        wrapper_function = init_modules()
        self.assertEqual(environ['MODULEPATH'], '')
        self.assertEqual(environ['LOADEDMODULES'], '')
        self.restore_env(('MODULEPATH', 'LOADEDMODULES'))
        self.cache_env(('MODULEPATH',))
        self.assertEqual(environ['MODULESHOME'], self.data_dir)
        self.assertNotIn('MODULEPATH', environ)
        mkdir(join(self.data_dir, 'init'))
        with open(join(self.data_dir, 'init', '.modulespath'), 'w') as p:
            p.write("#\n/foo\n/bar\n")
        wrapper_function = init_modules()
        self.assertEqual(environ['MODULEPATH'], '/foo:/bar')
        del environ['MODULEPATH']
        remove(join(self.data_dir, 'init', '.modulespath'))
        with open(join(self.data_dir, 'init', 'modulerc'), 'w') as p:
            p.write("#\nmodule use /foo\nmodule use /bar\n")
        wrapper_function = init_modules()
        self.assertEqual(environ['MODULEPATH'], '/foo:/bar')
        del environ['MODULEPATH']
        remove(join(self.data_dir, 'init', 'modulerc'))
        rmdir(join(self.data_dir, 'init'))
        self.restore_env(('MODULEPATH',))
        #
        # Base Module command
        #
        self.cache_env(('MODULE_VERSION', 'MODULE_VERSION_STACK', 'TCLSH'))
        modulecmd = init_modules(command=True)
        self.assertListEqual(modulecmd, ['/usr/bin/modulecmd', 'python'])
        tclfile = join(self.data_dir, 'modulecmd.tcl')
        with open(tclfile, 'w') as tcl:
            tcl.write('#!/usr/bin/tclsh\nputs "foo"\n')
        modulecmd = init_modules(command=True)
        self.assertListEqual(modulecmd, ['/usr/bin/tclsh', tclfile, 'python'])
        environ['TCLSH'] = '/opt/local/bin/tclsh'
        modulecmd = init_modules(command=True)
        self.assertListEqual(modulecmd, ['/opt/local/bin/tclsh', tclfile,
                                         'python'])
        del environ['TCLSH']
        self.restore_env(('TCLSH',))
        remove(tclfile)
        environ['MODULE_VERSION'] = '1.2.3.4'
        modulecmd = init_modules(command=True)
        self.assertListEqual(modulecmd, ['/opt/modules/1.2.3.4/bin/modulecmd',
                                         'python'])
        self.assertEqual(environ['MODULE_VERSION'],
                         environ['MODULE_VERSION_STACK'])
        del environ['MODULE_VERSION_STACK']
        del environ['MODULE_VERSION']
        self.restore_env(('MODULE_VERSION', 'MODULE_VERSION_STACK'))
        #
        # Standard functionality.
        #
        wrapper_function = init_modules()
        self.assertTrue(callable(wrapper_function))
        wrapper_method = init_modules(method=True)
        self.module = MethodType(wrapper_method, self)
        self.assertTrue(callable(self.module))
        self.assertEqual(wrapper_function.__doc__, self.module.__doc__)
        #
        # Test the generated function.
        #
        # self.assertEqual(environ['MODULEPATH'], '')
        # self.module('use', '/foo')
        # self.module('use', '/bar')
        # self.assertEqual(environ['MODULEPATH'], '/foo:/bar')
        # environ['MODULEPATH'] = ''

    def test_configure_module(self):
        """Test detection of directories for module configuration.
        """
        test_dirs = ('bin', 'lib', 'pro', 'py')
        results = {
            'name': 'foo',
            'version': 'bar',
            'product_root': '/my/product/root',
            'needs_bin': '',
            'needs_python': '',
            'needs_trunk_py': '# ',
            'trunk_py_dir': '/py',
            'needs_ld_lib': '',
            'needs_idl': '',
            'pyversion': "python{0:d}.{1:d}".format(*version_info)
            }
        for t in test_dirs:
            mkdir(join(self.data_dir, t))
        conf = configure_module('foo', 'bar', '/my/product/root',
                                working_dir=self.data_dir)
        for key in results:
            self.assertEqual(conf[key], results[key])
        #
        #
        #
        results['needs_python'] = '# '
        results['needs_trunk_py'] = ''
        conf = configure_module('foo', 'bar', '/my/product/root',
                                working_dir=self.data_dir,
                                dev=True)
        for key in results:
            self.assertEqual(conf[key], results[key])
        for t in test_dirs:
            rmdir(join(self.data_dir, t))
        #
        #
        #
        test_dirs = ('foo',)
        test_files = {'setup.cfg': "[entry_points]\nfoo.exe = foo.main:main\n",
                      'setup.py': '#!/usr/bin/env python\n'}
        for t in test_dirs:
            mkdir(join(self.data_dir, t))
        for t in test_files:
            with open(join(self.data_dir, t), 'w') as s:
                s.write(test_files[t])
        results['needs_bin'] = ''
        results['needs_python'] = ''
        results['needs_trunk_py'] = '# '
        results['needs_ld_lib'] = '# '
        results['needs_idl'] = '# '
        conf = configure_module('foo', 'bar', '/my/product/root',
                                working_dir=self.data_dir)
        results['needs_python'] = '# '
        results['needs_trunk_py'] = ''
        results['trunk_py_dir'] = ''
        conf = configure_module('foo', 'bar', '/my/product/root',
                                working_dir=self.data_dir,
                                dev=True)
        for key in results:
            self.assertEqual(conf[key], results[key])
        for t in test_dirs:
            rmdir(join(self.data_dir, t))
        for t in test_files:
            remove(join(self.data_dir, t))

    def test_process_module(self):
        """Test processing of module file templates.
        """
        module_file = join(self.data_dir, 'test.module')
        module_keywords = {'name': 'foo', 'version': 'bar'}
        process_module(module_file, module_keywords, self.data_dir)
        self.assertTrue(isdir(join(self.data_dir, 'foo')))
        self.assertTrue(exists(join(self.data_dir, 'foo', 'bar')))
        with open(join(self.data_dir, 'foo', 'bar')) as t:
            data = t.read()
        self.assertEqual(data, "foo\nbar\n")
        #
        # Clean up
        #
        remove(join(self.data_dir, 'foo', 'bar'))
        rmdir(join(self.data_dir, 'foo'))

    def test_default_module(self):
        """Test installation of .version files.
        """
        mkdir(join(self.data_dir, 'foo'))
        module_keywords = {'name': 'foo', 'version': 'bar'}
        default_module(module_keywords, self.data_dir)
        self.assertTrue(exists(join(self.data_dir, 'foo', '.version')))
        with open(join(self.data_dir, 'foo', '.version')) as t:
            data = t.read()
        self.assertEqual(data, '#%Module1.0\nset ModulesVersion "bar"\n')
        #
        # Clean up
        #
        remove(join(self.data_dir, 'foo', '.version'))
        rmdir(join(self.data_dir, 'foo'))
