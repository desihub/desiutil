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
import logging
import re
from logging.handlers import MemoryHandler
from subprocess import Popen, PIPE
from datetime import date
from types import MethodType
from os import chdir, environ, getcwd, makedirs, remove, symlink
from os.path import abspath, basename, exists, isdir, join
from shutil import copyfile, copytree, rmtree
from .git import last_tag
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

    Parameters
    ----------
    test : :class:`bool`, optional
        If ``True`` log messages will be supressed for testing purposes.

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

    def __init__(self, test=False):
        """Bare-bones initialization.

        The only thing done here is setting up the logging infrastructure.
        """
        self.executable = basename(argv[0])
        self.test = test
        if self.test:
            nh = logging.NullHandler()
            mh = MemoryHandler(1000000, flushLevel=logging.CRITICAL, target=nh)
            logging.getLogger(__name__).addHandler(mh)
        else:  # pragma: no cover
            logging.basicConfig(format=self.executable +
                                ' [%(name)s] Log - %(levelname)s: %(message)s',
                                datefmt='%Y-%m-%dT%H:%M:%S')
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
        log = logging.getLogger(__name__ + '.DesiInstall.get_options')
        check_env = {'MODULESHOME': None,
                     'DESI_PRODUCT_ROOT': None,
                     'USER': None,
                     'LANG': None}
        for e in check_env:
            try:
                check_env[e] = environ[e]
            except KeyError:
                if e == 'DESI_PRODUCT_ROOT' and 'NERSC_HOST' in environ:
                    log.debug('The environment variable DESI_PRODUCT_ROOT ' +
                              'is not set, but this is probably not a ' +
                              'problem at NERSC.')
                else:
                    log.warning(('The environment variable {0} is not ' +
                                'set!').format(e))
        parser = ArgumentParser(description="Install DESI software.",
                                prog=self.executable)
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
            self.options = parser.parse_args(test_args)
        self.ll = logging.INFO
        if self.options.verbose or self.options.test or self.test:
            self.ll = logging.DEBUG
        logging.getLogger(__name__).setLevel(self.ll)
        if test_args is not None:
            log.debug('Called parse_args() with: {0}'.format(
                      ' '.join(test_args)))
        log.debug('Set log level to {0}.'.format(
                  logging.getLevelName(self.ll)))
        self.config = None
        if self.options.config_file:
            log.debug("Detected configuration file: {0}.".format(self.options.config_file))
            c = SafeConfigParser()
            status = c.read([self.options.config_file])
            if status[0] == self.options.config_file:
                self.config = c
                log.debug("Successfully parsed {0}.".format(self.options.config_file))
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
        log = logging.getLogger(__name__ + '.DesiInstall.sanity_check')
        if (self.options.product == 'NO PACKAGE' or
                self.options.product_version == 'NO VERSION'):
            if self.options.bootstrap:
                self.options.default = True
                self.options.product = 'desiutil'
                self.options.product_version = last_tag('desihub', 'desiutil')
                log.info("Selected desiutil/{0} for installation.".format(
                         self.options.product_version))
            else:
                message = "You must specify a product and a version!"
                log.critical(message)
                raise DesiInstallException(message)
        if (self.options.moduleshome is None or
                not isdir(self.options.moduleshome)):
            message = "You do not appear to have Modules set up."
            log.critical(message)
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
        log = logging.getLogger(__name__ + '.DesiInstall.get_product_version')
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
            log.warning('Guessing {0} is at {1}.'.format(
                self.baseproduct, self.fullproduct))
            log.warning('Add location to desiutil.install.known_products ' +
                        'if that is incorrect.')
        self.baseversion = basename(self.options.product_version)
        self.github = False
        if 'github.com' in self.fullproduct:
            self.github = True
            log.debug("Detected GitHub install.")
        return (self.fullproduct, self.baseproduct, self.baseversion)

    def identify_branch(self):
        """If this is not a tag install, determine whether this is a trunk
        or branch install.

        Returns
        -------
        :class:`str`
            The full path to the branch/tag/trunk/master code.
        """
        log = logging.getLogger(__name__ + '.DesiInstall.identify_branch')
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
        log.debug("Using {0} as the URL of this product.".format(
                  self.product_url))
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
        log = logging.getLogger(__name__ + '.DesiInstall.verify_url')
        if self.github:
            try:
                r = requests.head(self.product_url)
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                message = ("Error {0:d} querying GitHub URL: " +
                           "{1}.").format(r.status_code, self.product_url)
                log.critical(message)
                raise DesiInstallException(message)
        else:
            command = [svn, '--non-interactive', '--username',
                       self.options.username, 'ls', self.product_url]
            log.debug(' '.join(command))
            proc = Popen(command, universal_newlines=True,
                         stdout=PIPE, stderr=PIPE)
            out, err = proc.communicate()
            log.debug(out)
            if len(err) > 0:
                message = ("svn error while testing product URL: " +
                           "{0}.").format(err)
                log.critical(message)
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
        log = logging.getLogger(__name__ + '.DesiInstall.get_code')
        self.working_dir = join(abspath('.'), '{0}-{1}'.format(
                                self.baseproduct, self.baseversion))
        if isdir(self.working_dir):
            log.info(("Detected old working directory, {0}. " +
                     "Deleting...").format(self.working_dir))
            log.debug("rmtree('{0}')".format(self.working_dir))
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
                        log.critical(message)
                        raise DesiInstallException(message)
                command = ['git', 'clone', '-q', self.product_url,
                           self.working_dir]
                log.debug(' '.join(command))
                if self.options.test:
                    out, err = 'Test Mode.', ''
                else:
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                log.debug(out)
                if len(err) > 0:
                    message = ("git error while downloading product code: " +
                               err)
                    log.critical(message)
                    raise DesiInstallException(message)
                if self.is_branch:
                    original_dir = getcwd()
                    log.debug("chdir('{0}')".format(self.working_dir))
                    if not self.options.test:
                        chdir(self.working_dir)
                    command = ['git', 'checkout', '-q', '-b', self.baseversion,
                               'origin/'+self.baseversion]
                    log.debug(' '.join(command))
                    if self.options.test:
                        out, err = 'Test Mode.', ''
                    else:
                        proc = Popen(command, universal_newlines=True,
                                     stdout=PIPE, stderr=PIPE)
                        out, err = proc.communicate()
                    log.debug(out)
                    if len(err) > 0:
                        message = ("git error while changing branch:" +
                                   " {0}".format(err))
                        log.critical(message)
                        raise DesiInstallException(message)
                    log.debug("chdir('{0}')".format(original_dir))
                    if not self.options.test:
                        chdir(original_dir)
            else:
                if self.options.test:
                    log.debug("Test Mode. Skipping download of {0}".format(
                              self.product_url))
                else:
                    try:
                        r = requests.get(self.product_url)
                        r.raise_for_status()
                    except requests.exceptions.HTTPError:
                        message = ("Error while downloading {0}, " +
                                   "HTTP response was {1:d}.").format(
                                   self.product_url, r.status_code)
                        log.critical(message)
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
                        log.critical(message)
                        raise DesiInstallException(message)
        else:
            if self.is_trunk or self.is_branch:
                get_svn = 'checkout'
            else:
                get_svn = 'export'
            command = ['svn', '--non-interactive', '--username',
                       self.options.username, get_svn, self.product_url,
                       self.working_dir]
            log.debug(' '.join(command))
            if self.options.test:
                out, err = 'Test Mode.', ''
            else:
                proc = Popen(command, universal_newlines=True,
                             stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
            log.debug(out)
            if len(err) > 0:
                message = ("svn error while downloading product " +
                           "code: {0}".format(err))
                log.critical(message)
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
        log = logging.getLogger(__name__ + '.DesiInstall.build_type')
        build_type = set(['plain'])
        if self.options.force_build_type:
            log.debug("Forcing build type: make")
            build_type.add('make')
        else:
            if exists(join(self.working_dir, 'setup.py')):
                log.debug("Detected build type: py")
                build_type.add('py')
            if exists(join(self.working_dir, 'Makefile')):
                log.debug("Detected build type: make")
                build_type.add('make')
            else:
                if isdir(join(self.working_dir, 'src')):
                    log.debug("Detected build type: src")
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
        log = logging.getLogger(__name__ + '.DesiInstall.set_install_dir')
        try:
            self.nersc = environ['NERSC_HOST']
        except KeyError:
            self.nersc = None
        if self.options.root is None or not isdir(self.options.root):
            if self.nersc is not None:
                self.options.root = self.default_nersc_dir()
            else:
                message = "DESI_PRODUCT_ROOT is missing or not set."
                log.critical(message)
                raise DesiInstallException(message)
        self.install_dir = join(self.options.root, 'code', self.baseproduct,
                                self.baseversion)
        if isdir(self.install_dir) and not self.options.test:
            if self.options.force:
                log.debug("rmtree('{0}')".format(self.install_dir))
                if not self.options.test:
                    rmtree(self.install_dir)
            else:
                message = ("Install directory, {0}, already exists!".format(
                           self.install_dir))
                log.critical(message)
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
        log = logging.getLogger(__name__ + '.DesiInstall.start_modules')
        initpy_found = False
        module_method = init_modules(self.options.moduleshome, method=True)
        if module_method is None:
            message = ("Could not initialize Modules with MODULESHOME={0}!".format(
                       self.options.moduleshome))
            log.critical(message)
            raise DesiInstallException(message)
        else:
            log.debug("Initializing Modules with MODULESHOME={0}.".format(
                      self.options.moduleshome))
            self.module = MethodType(module_method, self)
        return True

    def module_dependencies(self):
        """Figure out the dependencies and load them.

        Returns
        -------
        :class:`list`
            The list of dependencies.
        """
        log = logging.getLogger(__name__ + '.DesiInstall.module_dependencies')
        self.module_file = join(self.working_dir, 'etc',
                                self.baseproduct + '.module')
        if not exists(self.module_file):
            try:
                self.module_file = join(environ['DESIUTIL'], 'etc',
                                        'desiutil.module')
            except KeyError:
                message = ("DESIUTIL is not set.  " +
                           "Is desiutil installed and loaded?")
                log.critical(message)
                raise DesiInstallException(message)
        if self.options.test:
            log.debug('Test Mode. Skipping loading of dependencies.')
            self.deps = list()
        else:
            self.deps = dependencies(self.module_file)
            for d in self.deps:
                base_d = d.split('/')[0]
                if base_d in environ['LOADEDMODULES']:
                    m_command = 'switch'
                else:
                    m_command = 'load'
                log.debug("module('{0}', '{1}')".format(m_command, d))
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
                nersc_module = self.default_nersc_dir_templates[self.nersc].format(desiconda_version='startup')
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
        log = logging.getLogger(__name__ + '.DesiInstall.install_module')
        dev = False
        if 'py' in self.build_type:
            if self.is_trunk or self.is_branch:
                dev = True
        else:
            if isdir(join(self.working_dir, 'py')):
                dev = True
        log.debug(("configure_module({0}, {1}, working_dir={2}, " +
                  "dev={3})").format(self.baseproduct, self.baseversion,
                  self.working_dir, dev))
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
                log.debug("nersc_module_dir set to {0}.".format(self.options.moduledir))
            if not self.options.test:
                if not isdir(self.options.moduledir):
                    log.info("Creating Modules directory {0}.".format(
                             self.options.moduledir))
                    try:
                        makedirs(self.options.moduledir)
                    except OSError as ose:
                        log.critical(ose.strerror)
                        raise DesiInstallException(ose.strerror)
        if self.options.test:
            log.debug("Test Mode. Skipping Module file installation.")
            mod = ''
        else:
            try:
                log.debug(("process_module('{0}', self.module_keywords, " +
                           "'{1}')").format(self.module_file,
                                            self.options.moduledir))
                mod = process_module(self.module_file, self.module_keywords,
                                     self.options.moduledir)
            except OSError as ose:
                log.critical(ose.strerror)
                raise DesiInstallException(ose.strerror)
            if self.options.default:
                log.debug(("default_module(self.module_keywords, " +
                           "'{0}')".format(self.options.moduledir)))
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
        log = logging.getLogger(__name__ + '.DesiInstall.prepare_environment')
        environ['WORKING_DIR'] = self.working_dir
        environ['INSTALL_DIR'] = self.install_dir
        if self.baseproduct == 'desiutil':
            environ['DESIUTIL'] = self.install_dir
        else:
            if self.baseproduct in environ['LOADEDMODULES']:
                m_command = 'switch'
            else:
                m_command = 'load'
            log.debug("module('{0}', '{1}/{2}')".format(m_command,
                      self.baseproduct, self.baseversion))
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
        log = logging.getLogger(__name__ + '.DesiInstall.get_extra')
        extra_script = join(self.working_dir, 'etc',
                            '{0}_data.sh'.format(self.baseproduct))
        if self.options.test:
            log.debug('Test Mode. Skipping install of extra data.')
        else:
            if exists(extra_script):
                log.debug("Detected extra script: {0}.".format(extra_script))
                proc = Popen([extra_script], universal_newlines=True,
                             stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                status = proc.returncode
                log.debug(out)
                # Temporarily ignore all error messages from script.
                # if status != 0 and len(err) > 0:
                #     message = "Error grabbing extra data: {0}".format(err)
                #     log.critical(message)
                #     raise DesiInstallException(message)
        return

    def copy_install(self):
        """Simply copying the files from the checkout to the install.

        Returns
        -------
        :class:`bool`
            Returns ``True``.
        """
        log = logging.getLogger(__name__ + '.DesiInstall.copy_install')
        log.debug("copytree('{0}', '{1}')".format(
                  self.working_dir, self.install_dir))
        if not self.options.test:
            copytree(self.working_dir, self.install_dir)
        return True

    def install(self):
        """Run setup.py, etc.
        """
        log = logging.getLogger(__name__ + '.DesiInstall.install')
        if (self.is_trunk or self.is_branch):
            if 'src' in self.build_type:
                if self.options.test:
                    log.debug("Test Mode. Skipping 'make'.")
                else:
                    chdir(self.install_dir)
                    command = ['make', '-C', 'src', 'all']
                    log.info('Running "{0}" in {1}.'.format(
                             ' '.join(command), self.install_dir))
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    log.debug(out)
                    if len(err) > 0:
                        message = "Error during compile: {0}".format(err)
                        log.critical(message)
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
                    log.debug(("Test Mode.  Skipping creation of " +
                               "{0}.").format(lib_dir))
                else:
                    try:
                        makedirs(lib_dir)
                    except OSError as ose:
                        log.critical(ose.strerror)
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
                log.debug(' '.join(command))
                if self.options.test:
                    log.debug("Test Mode.  Skipping 'python setup.py install'.")
                else:
                    chdir(self.working_dir)
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    log.debug(out)
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
                            log.critical(message)
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
                log.debug(' '.join(command))
                if self.options.test:
                    log.debug("Test Mode.  Skipping 'make install'.")
                else:
                    if 'src' in self.build_type:
                        chdir(self.install_dir)
                    else:
                        chdir(self.working_dir)
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    log.debug(out)
                    if len(err) > 0:
                        message = "Error during compile: {0}".format(err)
                        log.critical(message)
                        raise DesiInstallException(message)
        return

    def cross_install(self):
        """Make package available on multiple hosts.

        Returns
        -------
        :class:`list`
            A list of the symlinks created.
        """
        log = logging.getLogger(__name__ + '.DesiInstall.cross_install')
        links = list()
        if self.options.cross_install:
            cross_install_host = self.cross_install_host
            nersc_hosts = self.nersc_hosts
            if self.config is not None:
                if self.config.has_option("Cross Install",
                                          'cross_install_host'):
                    cross_install_host = self.config.get("Cross Install",
                                                         'cross_install_host')
                    log.debug("cross_install_host set to {0}.".format(cross_install_host))
                if self.config.has_option("Cross Install", 'nersc_hosts'):
                    nersc_hosts = self.config.get("Cross Install",
                                                  'nersc_hosts').split(',')
                    log.debug("nersc_hosts set to {0}.".format(", ".join(nersc_hosts)))
            if self.nersc is None:
                log.error("Cross-installs are only supported at NERSC.")
            elif self.nersc != cross_install_host:
                log.error("Cross-installs should be performed on {0}.".format(
                          cross_install_host))
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
                    log.debug("symlink('{0}', '{1}')".format(s, d))
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
        log = logging.getLogger(__name__+'.DesiInstall.permissions')
        command = ['fix_permissions.sh']
        if self.options.verbose:
            command.append('-v')
        if self.options.test:
            command.append('-t')
        command.append(self.install_dir)
        log.debug(' '.join(command))
        proc = Popen(command, universal_newlines=True,
                     stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        status = proc.returncode
        log.debug(out)
        return status

    def cleanup(self):
        """Clean up after the install.

        Returns
        -------
        :class:`bool`
            Returns ``True``
        """
        log = logging.getLogger(__name__+'.DesiInstall.cleanup')
        log.debug("chdir('{0}')".format(self.original_dir))
        if not self.options.test:
            chdir(self.original_dir)
        if not self.options.keep:
            log.debug("rmtree('{0}')".format(self.working_dir))
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
        log = logging.getLogger(__name__ + '.DesiInstall.run')
        log.debug('Commencing run().')
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
        log.debug('run() complete.')
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
