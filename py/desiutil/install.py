# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
================
desiutil.install
================

This package contains code for installing DESI software products.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
from sys import argv, executable, path, version_info
import requests
import tarfile
import re
from subprocess import Popen, PIPE
from datetime import date
from types import MethodType
from os import chdir, environ, getcwd, makedirs, remove, symlink
from os.path import abspath, basename, exists, isdir, join
from shutil import copyfile, copytree, rmtree
from .git import last_tag
from .log import get_logger, DEBUG, INFO
from .modules import (init_modules, configure_module,
                      process_module, default_module)
from . import __version__ as desiutilVersion

try:
    # Python 3
    from io import BytesIO as StringIO
except ImportError:
    # Python 2
    from cStringIO import StringIO

try:
    # Python 3
    from configparser import ConfigParser as SafeConfigParser
except ImportError:
    # Python 2
    from ConfigParser import SafeConfigParser


known_products = {
    'desiBackup': 'https://github.com/desihub/desiBackup',
    'desidatamodel': 'https://github.com/desihub/desidatamodel',
    'desietc': 'https://github.com/desihub/desietc',
    'desimodel': 'https://github.com/desihub/desimodel',
    'desimodules': 'https://github.com/desihub/desimodules',
    'desisim': 'https://github.com/desihub/desisim',
    'desispec': 'https://github.com/desihub/desispec',
    'desisurvey': 'https://github.com/desihub/desisurvey',
    'desitarget': 'https://github.com/desihub/desitarget',
    'desitemplate': 'https://github.com/desihub/desitemplate',
    'desitemplate_cpp': 'https://github.com/desihub/desitemplate_cpp',
    'desitree': 'https://github.com/desihub/desitree',
    'desiutil': 'https://github.com/desihub/desiutil',
    'fiberassign': 'https://github.com/desihub/fiberassign',
    'fiberassign_sqlite': 'https://github.com/desihub/fiberassign_sqlite',
    'imaginglss': 'https://github.com/desihub/imaginglss',
    'redmonster': 'https://github.com/desihub/redmonster',
    'specex': 'https://github.com/desihub/specex',
    'speclite': 'https://github.com/dkirkby/speclite',
    'specsim': 'https://github.com/desihub/specsim',
    'specter': 'https://github.com/desihub/specter',
    'bbspecsim': 'https://desi.lbl.gov/svn/code/spectro/bbspecsim',
    'desiAdmin': 'https://desi.lbl.gov/svn/code/tools/desiAdmin',
    'dspecsim': 'https://desi.lbl.gov/svn/code/spectro/dspecsim',
    'elg_deep2': 'https://desi.lbl.gov/svn/code/targeting/elg_deep2',
    'plate_layout': 'https://desi.lbl.gov/svn/code/focalplane/plate_layout',
    'positioner_control':
        'https://desi.lbl.gov/svn/code/focalplane/positioner_control',
    'templates': 'https://desi.lbl.gov/svn/code/spectro/templates',
    }


def dependencies(modulefile):
    """Process the dependencies for a software product.

    Parameters
    ----------
    modulefile : :class:`str`
        Name of the module file containing dependencies.

    Returns
    -------
    :class:`list`
        Returns the list of dependencies.  If the module file
        is not found or there are no dependencies, the list will be empty.

    Raises
    ------
    ValueError
        If `modulefile` can't be found.
    """
    nersc = 'NERSC_HOST' in environ
    if exists(modulefile):
        with open(modulefile) as m:
            lines = m.readlines()
        raw_deps = [l.strip().split()[2] for l in lines if
                    l.strip().startswith('module load')]
    else:
        raise ValueError("Modulefile {0} does not exist!".format(modulefile))
    if nersc:
        hpcp_deps = [d for d in raw_deps if '-hpcp' in d]
        for d in hpcp_deps:
            nd = d.replace("-hpcp", "")
            try:
                raw_deps.remove(nd)
            except ValueError:
                pass
        return raw_deps
    else:
        deps = [d for d in raw_deps if '-hpcp' not in d]
        return deps


class DesiInstallException(Exception):
    """The methods of :class:`DesiInstall` should raise this exception
    to indicate that the command-line script should exit immediately.
    """
    pass


class DesiInstall(object):
    """Code and data that drive the desiInstall script.

    Attributes
    ----------
    baseproduct : :class:`str`
        The bare name of the product, *e.g.* "desiutil".
    baseversion : :class:`str`
        The bare version, without any ``branches/`` qualifiers.
    config : :class:`~ConfigParser.SafeConfigParser`
        If an *optional* configuration file is specified on the command-line,
        this holds the object that reads it.
    cross_install_host : :class:`str`
        The NERSC host on which to perform cross-installs.
    default_nersc_dir_templates : :class:`dict`
        The default code and Modules install directory for every NERSC host.
    executable : :class:`str`
        The command used to invoke the script.
    fullproduct : :class:`str`
        The path to the product including its URL, *e.g.*,
        "https://github.com/desihub/desiutil".
    github : :class:`bool`
        ``True`` if the selected product lives on GitHub.
    is_branch : :class:`bool`
        ``True`` if a branch has been selected.
    is_trunk : :class:`bool`
        ``True`` if trunk or the master branch has been selected.
    ll : :class:`int`
        The log level.
    nersc : :class:`str`
        Holds the value of :envvar:`NERSC_HOST`, or ``None`` if not defined.
    nersc_hosts : :func:`tuple`
        The list of NERSC host names to be used for cross-installs.
    options : :class:`argparse.Namespace`
        The parsed command-line options.
    product_url : :class:`str`
        The URL that will be used to download the code.  This differs from
        `fullproduct` in that it includes the tag or branch name.
    test : :class:`bool`
        Captures the value of the `test` argument passed to the constructor.
    """
    cross_install_host = 'edison'
    nersc_hosts = ('cori', 'edison', 'datatran', 'scigate')
    default_nersc_dir_templates = {'edison': '/global/common/edison/contrib/desi/desiconda/{desiconda_version}',
                                   'cori': '/global/common/cori/contrib/desi/desiconda/{desiconda_version}',
                                   'datatran': '/global/project/projectdirs/desi/software/datatran/desiconda/{desiconda_version}',
                                   'scigate': '/global/project/projectdirs/desi/software/scigate/desiconda/{desiconda_version}'}

    def __init__(self):
        """Bare-bones initialization.

        The only thing done here is setting up the logging infrastructure.
        """
        self.log = get_logger(INFO, timestamp=True)
        return

    def get_options(self, test_args=None):
        """Parse command-line arguments passed to the desiInstall script.

        Parameters
        ----------
        test_args : :class:`list`
            Normally, this method is called without arguments, and
            :data:`sys.argv` is parsed.  Arguments should only be passed for
            testing purposes.

        Returns
        -------
        :class:`argparse.Namespace`
            A simple object containing the parsed options.  Also, the
            attribute `options` is set.
        """
        from argparse import ArgumentParser
        check_env = {'MODULESHOME': None,
                     'DESI_PRODUCT_ROOT': None,
                     'USER': None,
                     'LANG': None}
        for e in check_env:
            try:
                check_env[e] = environ[e]
            except KeyError:
                if e == 'DESI_PRODUCT_ROOT' and 'NERSC_HOST' in environ:
                    self.log.info('The environment variable DESI_PRODUCT_ROOT ' +
                                  'is not set, but this is probably not a ' +
                                  'problem at NERSC.')
                else:
                    self.log.warning('The environment variable %s is not set!',
                                     e)
        parser = ArgumentParser(description="Install DESI software.",
                                prog=basename(argv[0]))
        parser.add_argument('-a', '--anaconda', action='store', dest='anaconda',
                            default=self.anaconda_version(), metavar='VERSION',
                            help="Set the version of the DESI+Anaconda software stack.")
        parser.add_argument('-b', '--bootstrap', action='store_true',
                            dest='bootstrap',
                            help=("Run in bootstrap mode to install the " +
                                  "desiutil product."))
        parser.add_argument('-C', '--compile-c', action='store_true',
                            dest='force_build_type',
                            help=("Force C/C++ install mode, even if a " +
                                  "setup.py file is detected (WARNING: " +
                                  "this is for experts only)."))
        parser.add_argument('-c', '--configuration', action='store',
                            dest='config_file', default='',
                            metavar='FILE',
                            help=("Override built-in configuration with " +
                                  "data from FILE."))
        parser.add_argument('-d', '--default', action='store_true',
                            dest='default',
                            help='Make this version the default version.')
        parser.add_argument('-F', '--force', action='store_true',
                            dest='force',
                            help=('Overwrite any existing installation of ' +
                                  'this product/version.'))
        parser.add_argument('-k', '--keep', action='store_true',
                            dest='keep',
                            help='Keep the exported build directory.')
        parser.add_argument('-m', '--module-home', action='store',
                            dest='moduleshome',
                            default=check_env['MODULESHOME'],
                            metavar='DIR',
                            help='Set or override the value of $MODULESHOME')
        parser.add_argument('-M', '--module-dir', action='store',
                            dest='moduledir',
                            default='',
                            metavar='DIR',
                            help="Install module files in DIR.")
        parser.add_argument('-r', '--root', action='store',
                            dest='root',
                            default=check_env['DESI_PRODUCT_ROOT'],
                            metavar='DIR',
                            help=('Set or override the value of ' +
                                  '$DESI_PRODUCT_ROOT'))
        parser.add_argument('-t', '--test', action='store_true',
                            dest='test',
                            help=('Test Mode..  Do not actually install ' +
                                  'anything.'))
        parser.add_argument('-U', '--username', action='store',
                            dest='username',
                            default=check_env['USER'],
                            metavar='USER',
                            help="Set svn username to USER.")
        parser.add_argument('-v', '--verbose', action='store_true',
                            dest='verbose',
                            help='Print extra information.')
        parser.add_argument('-V', '--version', action='version',
                            version='%(prog)s ' + desiutilVersion)
        parser.add_argument('-x', '--cross-install', action='store_true',
                            dest='cross_install',
                            help=('Make the install available on multiple ' +
                                  'systems (e.g. NERSC).'))
        parser.add_argument('product', nargs='?',
                            default='NO PACKAGE',
                            help='Name of product to install.')
        parser.add_argument('product_version', nargs='?',
                            default='NO VERSION',
                            help='Version of product to install.')
        if test_args is None:  # pragma: no cover
            self.options = parser.parse_args()
        else:
            self.log.debug('Called parse_args() with: %s', ' '.join(test_args))
            self.options = parser.parse_args(test_args)
        if self.options.verbose or self.options.test:
            self.log.setLevel(DEBUG)
            self.log.debug('Set log level to DEBUG.')
        self.config = None
        if self.options.config_file:
            self.log.debug("Detected configuration file: %s.",
                           self.options.config_file)
            c = SafeConfigParser()
            status = c.read([self.options.config_file])
            if status[0] == self.options.config_file:
                self.config = c
                self.log.debug("Successfully parsed %s.",
                               self.options.config_file)
        return self.options

    def sanity_check(self):
        """Sanity check the options.

        Returns
        -------
        :class:`bool`
            ``True`` if there were no problems.

        Raises
        ------
        DesiInstallException
            If any options don't make sense.
        """
        if (self.options.product == 'NO PACKAGE' or
                self.options.product_version == 'NO VERSION'):
            if self.options.bootstrap:
                self.options.default = True
                self.options.product = 'desiutil'
                self.options.product_version = last_tag('desihub', 'desiutil')
                self.log.info("Selected desiutil/%s for installation.",
                              self.options.product_version)
            else:
                message = "You must specify a product and a version!"
                self.log.critical(message)
                raise DesiInstallException(message)
        if (self.options.moduleshome is None or
                not isdir(self.options.moduleshome)):
            message = "You do not appear to have Modules set up."
            self.log.critical(message)
            raise DesiInstallException(message)
        return True

    def get_product_version(self):
        """Determine the base product and version information.

        Returns
        -------
        :func:`tuple`
            A tuple containing the base product name and version.

        Raises
        ------
        DesiInstallException
            If the product and version inputs didn't make sense.
        """
        if self.config is not None:
            if self.config.has_section("Known Products"):
                for name, value in self.config.items("Known Products"):
                    known_products[name] = value
        if '/' in self.options.product:
            self.baseproduct = basename(self.options.product)
        else:
            self.baseproduct = self.options.product
        try:
            self.fullproduct = known_products[self.baseproduct]
        except KeyError:
            self.fullproduct = 'https://github.com/desihub/{}'.format(
                    self.baseproduct)
            self.log.warning('Guessing %s is at %s.',
                             self.baseproduct, self.fullproduct)
            self.log.warning('Add location to desiutil.install.known_products ' +
                             'if that is incorrect.')
        self.baseversion = basename(self.options.product_version)
        self.github = False
        if 'github.com' in self.fullproduct:
            self.github = True
            self.log.debug("Detected GitHub install.")
        return (self.fullproduct, self.baseproduct, self.baseversion)

    def identify_branch(self):
        """If this is not a tag install, determine whether this is a trunk
        or branch install.

        Returns
        -------
        :class:`str`
            The full path to the branch/tag/trunk/master code.
        """
        self.is_branch = self.options.product_version.startswith('branches')
        self.is_trunk = (self.options.product_version == 'trunk' or
                         self.options.product_version == 'master')
        if self.is_trunk or self.is_branch:
            if self.github:
                self.product_url = self.fullproduct + '.git'
            else:
                self.product_url = join(self.fullproduct,
                                        self.options.product_version)
        else:
            if self.github:
                self.product_url = join(self.fullproduct, 'archive',
                                        self.options.product_version +
                                        '.tar.gz')
            else:
                self.product_url = join(self.fullproduct, 'tags',
                                        self.options.product_version)
        self.log.debug("Using %s as the URL of this product.",
                       self.product_url)
        return self.product_url

    def verify_url(self, svn='svn'):
        """Ensure that the download URL is valid.

        Parameters
        ----------
        svn : :class:`str`, optional
            The path to the subversion command.

        Returns
        -------
        :class:`bool`
            ``True`` if everything checked out OK.

        Raises
        ------
        DesiInstallException
            If the subversion URL could not be found.
        """
        if self.github:
            try:
                r = requests.head(self.product_url)
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                message = ("Error {0:d} querying GitHub URL: " +
                           "{1}.").format(r.status_code, self.product_url)
                self.log.critical(message)
                raise DesiInstallException(message)
        else:
            command = [svn, '--non-interactive', '--username',
                       self.options.username, 'ls', self.product_url]
            self.log.debug(' '.join(command))
            proc = Popen(command, universal_newlines=True,
                         stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            self.log.debug(out)
            if len(err) > 0:
                message = ("svn error while testing product URL: " +
                           "{0}.").format(err)
                self.log.critical(message)
                raise DesiInstallException(message)
        return True

    def get_code(self):
        """Actually download the code.

        Following the standard order of execution, this is the first method
        that might actually modify the system (by downloading code).

        Raises
        ------
        DesiInstallException
            If any download errors are detected.
        """
        self.working_dir = join(abspath('.'), '{0}-{1}'.format(
                                self.baseproduct, self.baseversion))
        if isdir(self.working_dir):
            self.log.info("Detected old working directory, %s. Deleting...",
                          self.working_dir)
            self.log.debug("rmtree('%s')", self.working_dir)
            if not self.options.test:
                rmtree(self.working_dir)
        if self.github:
            if self.is_trunk or self.is_branch:
                if self.is_branch:
                    try:
                        r = requests.get(join(self.fullproduct, 'tree',
                                         self.baseversion))
                        r.raise_for_status()
                    except requests.exceptions.HTTPError:
                        message = ("Branch {0} does not appear to exist. " +
                                   "HTTP response was {1:d}.").format(
                                   self.baseversion, r.status_code)
                        self.log.critical(message)
                        raise DesiInstallException(message)
                command = ['git', 'clone', '-q', self.product_url,
                           self.working_dir]
                self.log.debug(' '.join(command))
                if self.options.test:
                    out, err = 'Test Mode.', ''
                else:
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                self.log.debug(out)
                if len(err) > 0:
                    message = ("git error while downloading product code: " +
                               err)
                    self.log.critical(message)
                    raise DesiInstallException(message)
                if self.is_branch:
                    original_dir = getcwd()
                    self.log.debug("chdir('%s')", self.working_dir)
                    if not self.options.test:
                        chdir(self.working_dir)
                    command = ['git', 'checkout', '-q', '-b', self.baseversion,
                               'origin/'+self.baseversion]
                    self.log.debug(' '.join(command))
                    if self.options.test:
                        out, err = 'Test Mode.', ''
                    else:
                        proc = Popen(command, universal_newlines=True,
                                     stdout=PIPE, stderr=PIPE)
                        out, err = proc.communicate()
                    self.log.debug(out)
                    if len(err) > 0:
                        message = ("git error while changing branch:" +
                                   " {0}".format(err))
                        self.log.critical(message)
                        raise DesiInstallException(message)
                    self.log.debug("chdir('%s')", original_dir)
                    if not self.options.test:
                        chdir(original_dir)
            else:
                if self.options.test:
                    self.log.debug("Test Mode. Skipping download of %s.",
                                   self.product_url)
                else:
                    try:
                        r = requests.get(self.product_url)
                        r.raise_for_status()
                    except requests.exceptions.HTTPError:
                        message = ("Error while downloading {0}, " +
                                   "HTTP response was {1:d}.").format(
                                   self.product_url, r.status_code)
                        self.log.critical(message)
                        raise DesiInstallException(message)
                    try:
                        tgz = StringIO(r.content)
                        tf = tarfile.open(fileobj=tgz, mode='r:gz')
                        tf.extractall()
                        tf.close()
                        tgz.close()
                        self.working_dir = join(abspath('.'), '{0}-{1}'.format(
                                                self.baseproduct, self.baseversion))
                        if self.baseversion.startswith('v'):
                            nov = join(abspath('.'), '{0}-{1}'.format(
                                       self.baseproduct, self.baseversion[1:]))
                            if exists(nov):
                                self.working_dir = nov
                    except:
                        message = "tar error while expanding product code!"
                        self.log.critical(message)
                        raise DesiInstallException(message)
        else:
            if self.is_trunk or self.is_branch:
                get_svn = 'checkout'
            else:
                get_svn = 'export'
            command = ['svn', '--non-interactive', '--username',
                       self.options.username, get_svn, self.product_url,
                       self.working_dir]
            self.log.debug(' '.join(command))
            if self.options.test:
                out, err = 'Test Mode.', ''
            else:
                proc = Popen(command, universal_newlines=True,
                             stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
            self.log.debug(out)
            if len(err) > 0:
                message = ("svn error while downloading product " +
                           "code: {0}".format(err))
                self.log.critical(message)
                raise DesiInstallException(message)
        return

    @property
    def build_type(self):
        """Determine the build type.

        Returns
        -------
        :class:`set`
            A set containing the detected build types.
        """
        build_type = set(['plain'])
        if self.options.force_build_type:
            self.log.debug("Forcing build type: make")
            build_type.add('make')
        else:
            if exists(join(self.working_dir, 'setup.py')):
                self.log.debug("Detected build type: py")
                build_type.add('py')
            if exists(join(self.working_dir, 'Makefile')):
                self.log.debug("Detected build type: make")
                build_type.add('make')
            else:
                if isdir(join(self.working_dir, 'src')):
                    self.log.debug("Detected build type: src")
                    build_type.add('src')
        return build_type

    def anaconda_version(self):
        """Try to determine the exact DESI+Anaconda version from the
        environment.

        Returns
        -------
        :class:`str`
            The DESI+Anaconda version.
        """
        try:
            desiconda = environ['DESICONDA']
        except KeyError:
            return 'current'
        try:
            return basename(desiconda[:desiconda.index('/code/desiconda')])
        except ValueError:
            return 'current'

    def default_nersc_dir(self, nersc_host=None):
        """Set the directory where code will reside.

        Parameters
        ----------
        nersc_host : :class:`str`, optional
            Specify a NERSC host that might be different from the current host.

        Returns
        -------
        :class:`str`
            Path to the host-specific install directory.
        """
        if nersc_host is None:
            return self.default_nersc_dir_templates[self.nersc].format(desiconda_version=self.options.anaconda)
        return self.default_nersc_dir_templates[nersc_host].format(desiconda_version=self.options.anaconda)

    def set_install_dir(self):
        """Decide on an install directory.

        Returns
        -------
        :class:`str`
            The directory selected for installation.
        """
        try:
            self.nersc = environ['NERSC_HOST']
        except KeyError:
            self.nersc = None
        if self.options.root is None or not isdir(self.options.root):
            if self.nersc is not None:
                self.options.root = self.default_nersc_dir()
            else:
                message = "DESI_PRODUCT_ROOT is missing or not set."
                self.log.critical(message)
                raise DesiInstallException(message)
        self.install_dir = join(self.options.root, 'code', self.baseproduct,
                                self.baseversion)
        if isdir(self.install_dir) and not self.options.test:
            if self.options.force:
                self.log.debug("rmtree('%s')", self.install_dir)
                if not self.options.test:
                    rmtree(self.install_dir)
            else:
                message = ("Install directory, {0}, already exists!".format(
                           self.install_dir))
                self.log.critical(message)
                raise DesiInstallException(message)
        return self.install_dir

    def start_modules(self):
        """Set up the modules infrastructure.

        Returns
        -------
        :class:`bool`
            ``True`` if the modules infrastructure was initialized
            successfully.
        """
        initpy_found = False
        module_method = init_modules(self.options.moduleshome, method=True)
        if module_method is None:
            message = ("Could not initialize Modules with MODULESHOME={0}!".format(
                       self.options.moduleshome))
            self.log.critical(message)
            raise DesiInstallException(message)
        else:
            self.log.debug("Initializing Modules with MODULESHOME=%s.",
                           self.options.moduleshome)
            self.module = MethodType(module_method, self)
        return True

    def module_dependencies(self):
        """Figure out the dependencies and load them.

        Returns
        -------
        :class:`list`
            The list of dependencies.
        """
        self.module_file = join(self.working_dir, 'etc',
                                self.baseproduct + '.module')
        if not exists(self.module_file):
            try:
                self.module_file = join(environ['DESIUTIL'], 'etc',
                                        'desiutil.module')
            except KeyError:
                message = ("DESIUTIL is not set.  " +
                           "Is desiutil installed and loaded?")
                self.log.critical(message)
                raise DesiInstallException(message)
        if self.options.test:
            self.log.debug('Test Mode. Skipping loading of dependencies.')
            self.deps = list()
        else:
            self.deps = dependencies(self.module_file)
            for d in self.deps:
                base_d = d.split('/')[0]
                if base_d in environ['LOADEDMODULES']:
                    m_command = 'switch'
                else:
                    m_command = 'load'
                self.log.debug("module('%s', '%s')", m_command, d)
                self.module(m_command, d)
        return self.deps

    @property
    def nersc_module_dir(self):
        """The directory that contains Module directories at NERSC.
        """
        if not hasattr(self, 'nersc'):
            return None
        if self.nersc is None:
            return None
        else:
            if self.baseproduct == 'desimodules':
                nersc_module = join(self.default_nersc_dir_templates[self.nersc].format(desiconda_version='startup'),
                                    'modulefiles')
            else:
                nersc_module = join(self.default_nersc_dir(),
                                    'modulefiles')
        if not hasattr(self, 'config'):
            return nersc_module
        if self.config is not None:
            if self.config.has_option("Module Processing",
                                      'nersc_module_dir'):
                nersc_module = self.config.get("Module Processing",
                                               'nersc_module_dir')
            if self.config.has_option("Module Processing",
                                      '{0}_module_dir'.format(self.nersc)):
                nersc_module = self.config.get("Module Processing",
                                               '{0}_module_dir'.format(self.nersc))
        return nersc_module

    def install_module(self):
        """Process the module file.

        Returns
        -------
        :class:`str`
            The text of the processed module file.
        """
        dev = False
        if 'py' in self.build_type:
            if self.is_trunk or self.is_branch:
                dev = True
        else:
            if isdir(join(self.working_dir, 'py')):
                dev = True
        self.log.debug("configure_module(%s, %s, working_dir=%s, dev=%s)",
                       self.baseproduct, self.baseversion,
                       self.working_dir, dev)
        self.module_keywords = configure_module(self.baseproduct,
                                                self.baseversion,
                                                join(self.options.root, 'code'),
                                                working_dir=self.working_dir,
                                                dev=dev)
        if self.options.moduledir == '':
            #
            # We didn't set a module dir, so derive it from options.root
            #
            if self.nersc is None:
                self.options.moduledir = join(self.options.root, 'modulefiles')
            else:
                self.options.moduledir = self.nersc_module_dir
                self.log.debug("nersc_module_dir set to %s.",
                          self.options.moduledir)
            if not self.options.test:
                if not isdir(self.options.moduledir):
                    self.log.info("Creating Modules directory %s.",
                                  self.options.moduledir)
                    self.log.debug("makedirs('%s')", self.options.moduledir)
                    try:
                        makedirs(self.options.moduledir)
                    except OSError as ose:
                        self.log.critical(ose.strerror)
                        raise DesiInstallException(ose.strerror)
        if self.options.test:
            self.log.debug("Test Mode. Skipping Module file installation.")
            mod = ''
        else:
            try:
                self.log.debug(("process_module('%s', self.module_keywords, " +
                                "'%s')"), self.module_file,
                               self.options.moduledir)
                mod = process_module(self.module_file, self.module_keywords,
                                     self.options.moduledir)
            except OSError as ose:
                self.log.critical(ose.strerror)
                raise DesiInstallException(ose.strerror)
            if self.options.default:
                self.log.debug("default_module(self.module_keywords, '%s')",
                               self.options.moduledir)
                dot_version = default_module(self.module_keywords,
                                             self.options.moduledir)
        return mod

    def prepare_environment(self):
        """Prepare the environment for the install.

        Returns
        -------
        :class:`str`
            The current working directory.  Because we're about to change it.
        """
        environ['WORKING_DIR'] = self.working_dir
        environ['INSTALL_DIR'] = self.install_dir
        if self.baseproduct == 'desiutil':
            environ['DESIUTIL'] = self.install_dir
        else:
            if self.baseproduct in environ['LOADEDMODULES']:
                m_command = 'switch'
            else:
                m_command = 'load'
            self.log.debug("module('%s', '%s/%s')", m_command,
                           self.baseproduct, self.baseversion)
            if not self.options.test:
                self.module(m_command, self.baseproduct + '/' + self.baseversion)
        env_version = self.baseproduct.upper() + '_VERSION'
        # The current install script expects a version in the form of
        # branches/test-0.4 or tags/0.4.4 or trunk
        if env_version not in environ:
            environ[env_version] = 'tags/'+self.baseversion
        self.original_dir = getcwd()
        return self.original_dir

    def get_extra(self):
        """Download any additional data not included in the code repository.

        This is done here so that :envvar:`WORKING_DIR` is defined.
        """
        extra_script = join(self.working_dir, 'etc',
                            '{0}_data.sh'.format(self.baseproduct))
        if self.options.test:
            self.log.debug('Test Mode. Skipping install of extra data.')
        else:
            if exists(extra_script):
                self.log.debug("Detected extra script: %s.", extra_script)
                proc = Popen([extra_script], universal_newlines=True,
                             stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                status = proc.returncode
                self.log.debug(out)
                # Temporarily ignore all error messages from script.
                # if status != 0 and len(err) > 0:
                #     message = "Error grabbing extra data: {0}".format(err)
                #     self.log.critical(message)
                #     raise DesiInstallException(message)
        return

    def copy_install(self):
        """Simply copying the files from the checkout to the install.

        Returns
        -------
        :class:`bool`
            Returns ``True``.
        """
        self.log.debug("copytree('%s', '%s')", self.working_dir,
                       self.install_dir)
        if not self.options.test:
            copytree(self.working_dir, self.install_dir)
        return True

    def install(self):
        """Run setup.py, etc.
        """
        if (self.is_trunk or self.is_branch):
            if 'src' in self.build_type:
                if self.options.test:
                    self.log.debug("Test Mode. Skipping 'make'.")
                else:
                    chdir(self.install_dir)
                    command = ['make', '-C', 'src', 'all']
                    self.log.info('Running "%s" in %s.',
                                  ' '.join(command), self.install_dir)
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    self.log.debug(out)
                    if len(err) > 0:
                        message = "Error during compile: {0}".format(err)
                        self.log.critical(message)
                        raise DesiInstallException(message)
        else:
            #
            # Run a 'real' install
            #
            # chdir(self.working_dir)
            if 'py' in self.build_type:
                #
                # For Python installs, a site-packages directory needs to
                # exist.  We may need to manipulate sys.path to include this
                # directory.
                #
                lib_dir = join(self.install_dir, 'lib',
                               self.module_keywords['pyversion'],
                               'site-packages')
                if self.options.test:
                    self.log.debug("Test Mode.  Skipping creation of %s.",
                                   lib_dir)
                else:
                    self.log.debug("makedirs('%s')", lib_dir)
                    try:
                        makedirs(lib_dir)
                    except OSError as ose:
                        self.log.critical(ose.strerror)
                        raise DesiInstallException(ose.strerror)
                    if lib_dir not in path:
                        try:
                            newpythonpath = (lib_dir + ':' +
                                             environ['PYTHONPATH'])
                        except KeyError:
                            newpythonpath = lib_dir
                        environ['PYTHONPATH'] = newpythonpath
                        path.insert(int(path[0] == ''), lib_dir)
                #
                # Ready to python setup.py
                #
                command = [executable, 'setup.py', 'install',
                           '--prefix={0}'.format(self.install_dir)]
                self.log.debug(' '.join(command))
                if self.options.test:
                    self.log.debug("Test Mode.  Skipping 'python setup.py install'.")
                else:
                    chdir(self.working_dir)
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    self.log.debug(out)
                    if len(err) > 0:
                        #
                        # Some warnings can be produced by processing
                        # MANIFEST.in and not finding directories.  These
                        # can be ignored.
                        #
                        manifestre = re.compile(r"(warning: |)no" +
                                                r"( previously-included | )" +
                                                r"(directories|files)", re.I)
                        # manifestre = re.compile(r"no( previously-included| )" +
                        #                         r"( directories| files)" +
                        #                         r"( found| ) " +
                        #                         r"matching '[^']+'")
                        lines = [l for l in err.split('\n') if len(l) > 0 and
                                 manifestre.search(l) is None and
                                 'astropy_helpers' not in l and
                                 'astropy-helpers' not in l]
                        if len(lines) > 0:
                            message = ("Error during installation: " +
                                       "{0}".format("\n".join(lines)))
                            self.log.critical(message)
                            raise DesiInstallException(message)
            #
            # At this point either we have already completed a Python
            # installation or we still need to compile the C/C++ product
            # (we had to construct doc/Makefile first).
            #
            if 'make' in self.build_type or 'src' in self.build_type:
                if 'src' in self.build_type:
                    command = ['make', '-C', 'src', 'all']
                else:
                    command = ['make', 'install']
                self.log.debug(' '.join(command))
                if self.options.test:
                    self.log.debug("Test Mode.  Skipping 'make install'.")
                else:
                    if 'src' in self.build_type:
                        chdir(self.install_dir)
                    else:
                        chdir(self.working_dir)
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    self.log.debug(out)
                    if len(err) > 0:
                        message = "Error during compile: {0}".format(err)
                        self.log.critical(message)
                        raise DesiInstallException(message)
        return

    def cross_install(self):
        """Make package available on multiple hosts.

        Returns
        -------
        :class:`list`
            A list of the symlinks created.
        """
        links = list()
        if self.options.cross_install:
            cross_install_host = self.cross_install_host
            nersc_hosts = self.nersc_hosts
            if self.config is not None:
                if self.config.has_option("Cross Install",
                                          'cross_install_host'):
                    cross_install_host = self.config.get("Cross Install",
                                                         'cross_install_host')
                    self.log.debug("cross_install_host set to %s.",
                                   cross_install_host)
                if self.config.has_option("Cross Install", 'nersc_hosts'):
                    nersc_hosts = self.config.get("Cross Install",
                                                  'nersc_hosts').split(',')
                    self.log.debug("nersc_hosts set to %s.",
                                   ", ".join(nersc_hosts))
            if self.nersc is None:
                self.log.error("Cross-installs are only supported at NERSC.")
            elif self.nersc != cross_install_host:
                self.log.error("Cross-installs should be performed on %s.",
                               cross_install_host)
            else:
                for nh in nersc_hosts:
                    if nh == cross_install_host:
                        continue
                    dst = join(self.default_nersc_dir(nh), 'code',
                               self.baseproduct)
                    if not islink(dst):
                        src = join('..', cross_install_host,
                                   self.baseproduct)
                        links.append((src, dst))
                    dst = join(self.default_nersc_dir(nh), 'modulefiles',
                               self.baseproduct)
                    if not islink(dst):
                        src = join('..', cross_install_host,
                                   self.baseproduct)
                        links.append((src, dst))
                for s, d in links:
                    self.log.debug("symlink('%s', '%s')", s, d)
                    if not self.options.test:
                        symlink(s, d)
        return links

    def permissions(self):
        """Fix possible install permission errors.

        Returns
        -------
        :class:`int`
            Status code returned by fix_permissions.sh script.
        """
        command = ['fix_permissions.sh']
        if self.options.verbose:
            command.append('-v')
        if self.options.test:
            command.append('-t')
        command.append(self.install_dir)
        self.log.debug(' '.join(command))
        proc = Popen(command, universal_newlines=True,
                     stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        status = proc.returncode
        self.log.debug(out)
        return status

    def cleanup(self):
        """Clean up after the install.

        Returns
        -------
        :class:`bool`
            Returns ``True``
        """
        self.log.debug("chdir('%s')", self.original_dir)
        if not self.options.test:
            chdir(self.original_dir)
        if not self.options.keep:
            self.log.debug("rmtree('%s')", self.working_dir)
            if not self.options.test:
                rmtree(self.working_dir)
        return True

    def run(self):  # pragma: no cover
        """This method wraps all the standard steps of the desiInstall script.

        Returns
        -------
        :class:`int`
            An integer suitable for passing to :func:`sys.exit`.
        """
        self.log.debug('Commencing run().')
        self.get_options()
        try:
            self.sanity_check()
            fullproduct, baseproduct, baseversion = self.get_product_version()
            self.identify_branch()
            self.verify_url()
            self.get_code()
            # build_type = self.set_build_type()
            self.set_install_dir()
            self.start_modules()
            self.module_dependencies()
            self.install_module()
            self.prepare_environment()
            self.get_extra()
            self.copy_install()
            self.install()
            self.cross_install()
            self.permissions()
        except DesiInstallException:
            return 1
        self.cleanup()
        self.log.debug('run() complete.')
        return 0


def main():
    """Entry point for the desiInstall script.

    Returns
    -------
    :class:`int`
        Exit status that will be passed to :func:`sys.exit`.
    """
    di = DesiInstall()
    status = di.run()
    return status
