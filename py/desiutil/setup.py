# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
==============
desiutil.setup
==============

This package contains code that might be useful in DESI setup.py files.
"""
import re
import unittest
from os import environ, walk
from os.path import abspath, basename, exists, isdir, isfile, join
from sys import exit, version_info
from setuptools import Command
from setuptools.command.test import test as BaseTest
from pkg_resources import _namespace_packages
from distutils.log import DEBUG, INFO, WARN, ERROR
from .svn import version as svn_version
from .git import version as git_version
from .modules import configure_module, process_module, default_module


class DesiAPI(Command):
    """Generate an api.rst file.
    """
    description = "create/update doc/api.rst"
    user_options = [('api=', 'a',
                     'Set the name of the API file (default doc/api.rst).'),
                    ('overwrite', 'o',
                     'Overwrite the existing API file.')]
    boolean_options = ['overwrite']
    _exclude_file = ('_version.py',)

    def initialize_options(self):
        self.overwrite = False
        self.api = join(abspath('.'), 'doc', 'api.rst')

    def finalize_options(self):
        pass

    def run(self):
        n = self.distribution.metadata.get_name()
        productroot = find_version_directory(n)
        modules = []
        for dirpath, dirnames, filenames in walk(productroot):
            if dirpath == productroot:
                d = ''
            else:
                d = dirpath.replace(productroot + '/', '')
            self.announce(d, level=DEBUG)
            for f in filenames:
                mod = [n]
                if f.endswith('.py') and f not in self._exclude_file and not self._test_file(d, f):
                    if d:
                        mod += d.split('/')
                    if f != '__init__.py':
                        mod.append(f.replace('.py', ''))
                    modules.append('.'.join(mod))
                    self.announce('.'.join(mod), level=DEBUG)
        self._print(n, modules)

    def _print(self, name, modules):
        lines = []
        title = "{0} API".format(name)
        lines = ['='*len(title), title, '='*len(title), '']
        for m in sorted(modules):
            lines += ['.. automodule:: {0}'.format(m), '    :members:', '']
        if exists(self.api):
            if self.overwrite:
                self.announce("{0} will be overwritten!".format(self.api),
                              level=WARN)
            else:
                self.announce("{0} already exists!".format(self.api),
                              level=ERROR)
                exit(1)
        with open(self.api, 'w') as a:
            a.write('\n'.join(lines))

    def _test_file(self, d, f):
        return basename(d) == 'test' or basename(d) == 'tests'


class DesiModule(Command):
    """Allow users to install module files with
    ``python setup.py module_file``.
    """
    description = "install a module file for this package"
    user_options = [('default', 'd',
                     'Set this version as the default Module file.'),
                    ('modules=', 'm', 'Set the Module install directory.')
                    ]
    boolean_options = ['default']

    def initialize_options(self):
        self.modules = None
        self.default = False

    def finalize_options(self):
        if self.modules is None:
            try:
                self.modules = join('/global/common/software/desi',
                                    environ['NERSC_HOST'],
                                    'desiconda',
                                    'current',
                                    'modulefiles')
            except KeyError:
                try:
                    self.modules = join(environ['DESI_PRODUCT_ROOT'],
                                        'modulefiles')
                except KeyError:
                    self.announce("Could not determine a Module install directory!",
                                  level=ERROR)
                    exit(1)

    def run(self):
        meta = self.distribution.metadata
        name = meta.get_name()
        version = meta.get_version()
        dev = 'dev' in version
        working_dir = abspath('.')
        module_keywords = configure_module(name, version, dev=dev)
        module_file = join(working_dir, 'etc', '{0}.module'.format(name))
        if exists(module_file):
            process_module(module_file, module_keywords, self.modules)
        else:
            self.announce("Could not find a Module file: {0}.".format(module_file),
                          level=ERROR)
        if self.default:
            default_module(module_keywords, self.modules)
        return


class DesiTest(BaseTest, object):
    """Add coverage to test commands.
    """
    description = "run unit tests after in-place build"
    user_options = [('test-module=', 'm',
                     "Run 'test_suite' in specified module"),
                    ('test-suite=', 's',
                     "Test suite to run (e.g. 'some_module.test_suite')"),
                    ('test-runner=', 'r', "Test runner to use"),
                    ('coverage', 'c', ('Create a coverage report. ' +
                     'Requires the coverage package.'))
                    ]
    boolean_options = ['coverage']

    def initialize_options(self):
        self.coverage = False
        super(DesiTest, self).initialize_options()

    def finalize_options(self):
        if self.coverage:
            try:
                import coverage
            except ImportError:
                self.announce(("--coverage requires that the coverage " +
                               "package is installed, disabling coverage" +
                               "option."), level=WARN)
                self.coverage = False
        super(DesiTest, self).finalize_options()

    def run_tests(self):
        # Purge modules under test from sys.modules. The test loader will
        # re-import them from the build location. Required when 2to3 is used
        # with namespace packages.
        if getattr(self.distribution, 'use_2to3', False):
            module = self.test_args[-1].split('.')[0]
            if module in _namespace_packages:
                del_modules = []
                if module in sys.modules:
                    del_modules.append(module)
                module += '.'
                for name in sys.modules:
                    if name.startswith(module):
                        del_modules.append(name)
                list(map(sys.modules.__delitem__, del_modules))
        if self.coverage:
            self.announce("Coverage selected!", level=INFO)
            import coverage
            cov = coverage.coverage(data_file=abspath(".coverage"),
                                    config_file=abspath(".coveragerc"))
            cov.start()

        result = unittest.main(None, None,
                               ([unittest.__file__] + self.test_args),
                               testLoader=self._resolve_as_ep(self.test_loader),
                               testRunner=self._resolve_as_ep(self.test_runner),
                               exit=False)
        if result.result.wasSuccessful():
            if self.coverage:
                cov.stop()
                self.announce('Saving coverage data in .coverage...',
                              level=INFO)
                cov.save()
                self.announce('Saving HTML coverage report in htmlcov...',
                              level=INFO)
                cov.html_report(directory=abspath('htmlcov'))
        else:
            exit(1)


class DesiVersion(Command):
    """Allow users to easily update the package version with
    ``python setup.py version``.
    """
    description = "update _version.py from git repo"
    user_options = [('tag=', 't',
                     'Set the version to a name in preparation for tagging.'),
                    ]
    boolean_options = []

    def initialize_options(self):
        self.tag = None

    def finalize_options(self):
        pass

    def run(self):
        meta = self.distribution.metadata
        update_version(meta.get_name(), tag=self.tag)
        ver = get_version(meta.get_name())
        self.announce("Version is now {}.".format(ver), level=INFO)


def find_version_directory(productname):
    """Return the name of a directory containing version information.

    Looks for files in the following places:

    * py/`productname`/_version.py
    * `productname`/_version.py

    Parameters
    ----------
    productname : :class:`str`
        The name of the package.

    Returns
    -------
    :class:`str`
        Name of a directory that can or does contain version information.

    Raises
    ------
    IOError
        If no valid directory can be found.
    """
    setup_dir = abspath('.')
    if isdir(join(setup_dir, 'py', productname)):
        version_dir = join(setup_dir, 'py', productname)
    elif isdir(join(setup_dir, productname)):
        version_dir = join(setup_dir, productname)
    else:
        raise IOError("Could not find a directory containing version information!")
    return version_dir


def get_version(productname):
    """Get the value of ``__version__`` without having to import the module.

    Parameters
    ----------
    productname : :class:`str`
        The name of the package.

    Returns
    -------
    :class:`str`
        The value of ``__version__``.
    """
    ver = 'unknown'
    try:
        version_dir = find_version_directory(productname)
    except IOError:
        return ver
    version_file = join(version_dir, '_version.py')
    if not isfile(version_file):
        update_version(productname)
    with open(version_file, "r") as f:
        for line in f.readlines():
            mo = re.match("__version__ = '(.*)'", line)
            if mo:
                ver = mo.group(1)
    return ver


def update_version(productname, tag=None):
    """Update the _version.py file.

    Parameters
    ----------
    productname : :class:`str`
        The name of the package.
    tag : :class:`str`, optional
        Set the version to this string, unconditionally.

    Raises
    ------
    IOError
        If the repository type could not be determined.
    """
    version_dir = find_version_directory(productname)
    if tag is not None:
        ver = tag
    else:
        if isdir(".svn"):
            ver = svn_version(productname)
        elif isdir(".git"):
            ver = git_version()
        else:
            raise IOError("Could not determine repository type.")
    version_file = join(version_dir, '_version.py')
    with open(version_file, "w") as f:
        f.write("__version__ = '{}'\n".format(ver))
    return
