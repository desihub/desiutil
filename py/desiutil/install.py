# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
================
desiutil.install
================

This package contains code for installing DESI software products.
"""
import os
import sys
import tarfile
import stat
import shutil
import requests
from io import BytesIO
from subprocess import Popen, PIPE
from types import MethodType
from importlib.resources import files
from .git import last_tag
from .log import get_logger, DEBUG, INFO
from .modules import (init_modules, configure_module,
                      process_module, default_module)
from . import __version__ as desiutilVersion


known_products = {
    'desiBackup': 'https://github.com/desihub/desiBackup',
    'desicmx': 'https://github.com/desihub/desicmx',
    'desida': 'https://github.com/desihub/desida',
    'desidatamodel': 'https://github.com/desihub/desidatamodel',
    'desidithering': 'https://github.com/desihub/desidithering',
    'desietc': 'https://github.com/desihub/desietc',
    'desigal': 'https://github.com/desihub/desigal',
    'desilamps': 'https://github.com/desihub/desilamps',
    'desimeter': 'https://github.com/desihub/desimeter',
    'desimodel': 'https://github.com/desihub/desimodel',
    'desiperf': 'https://github.com/desihub/desiperf',
    'desisim': 'https://github.com/desihub/desisim',
    'desisim-testdata': 'https://github.com/desihub/desisim-testdata',
    'desispec': 'https://github.com/desihub/desispec',
    'desisurvey': 'https://github.com/desihub/desisurvey',
    'desitarget': 'https://github.com/desihub/desitarget',
    'desitemplate': 'https://github.com/desihub/desitemplate',
    'desitemplate_cpp': 'https://github.com/desihub/desitemplate_cpp',
    'desitest': 'https://github.com/desihub/desitest',
    'desitransfer': 'https://github.com/desihub/desitransfer',
    'desitree': 'https://github.com/desihub/desitree',
    'desiutil': 'https://github.com/desihub/desiutil',
    'fastspecfit': 'https://github.com/desihub/fastspecfit',
    'fiberassign': 'https://github.com/desihub/fiberassign',
    'gcr-catalogs': 'https://github.com/desihub/gcr-catalogs',
    'imaginglss': 'https://github.com/desihub/imaginglss',
    'LSS': 'https://github.com/desihub/LSS',
    'nightwatch': 'https://github.com/desihub/nightwatch',
    'prospect': 'https://github.com/desihub/prospect',
    'QuasarNP': 'https://github.com/desihub/QuasarNP',
    'quicksurvey_example': 'https://github.com/desihub/quicksurvey_example',
    'redrock': 'https://github.com/desihub/redrock',
    'redrock-templates': 'https://github.com/desihub/redrock-templates',
    'simqso': 'https://github.com/desihub/simqso',
    'specex': 'https://github.com/desihub/specex',
    'speclite': 'https://github.com/desihub/speclite',
    'specprod-db': 'https://github.com/desihub/specprod-db',
    'specsim': 'https://github.com/desihub/specsim',
    'specter': 'https://github.com/desihub/specter',
    'gpu_specter': 'https://github.com/desihub/gpu_specter',
    'surveysim': 'https://github.com/desihub/surveysim',
    'teststand': 'https://github.com/desihub/teststand',
    'tilepicker': 'https://github.com/desihub/tilepicker',
    'timedomain': 'https://github.com/desihub/timedomain',
    'plate_layout': 'https://desi.lbl.gov/svn/code/focalplane/plate_layout',
    'positioner_control': 'https://desi.lbl.gov/svn/code/focalplane/positioner_control'}


#
# Reserved for future use.
#
# pip_safe = frozenset(['desicmx', 'desidatamodel', 'desidithering', 'desietc',
#                       'desimeter', 'desimodel', 'desisim', 'desispec',
#                       'desisurvey', 'desitarget', 'desitemplate', 'desitransfer',
#                       'desiutil', 'fiberassign', 'prospect', 'redrock',
#                       'specex', 'speclite', 'specsim', 'specter', 'surveysim',
#                       'simqso'])


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
    if not os.path.exists(modulefile):
        raise ValueError("Modulefile {0} does not exist!".format(modulefile))
    with open(modulefile) as m:
        lines = m.readlines()
    return [ln.strip().split()[2] for ln in lines if
            ln.strip().startswith('module load')]


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
    default_nersc_dir_template : :class:`str`
        The default code and Modules install directory for every NERSC host.
    fullproduct : :class:`str`
        The path to the product including its URL, *e.g.*,
        "https://github.com/desihub/desiutil".
    github : :class:`bool`
        ``True`` if the selected product lives on GitHub.
    is_branch : :class:`bool`
        ``True`` if a branch has been selected.
    log : :class:`logging.Logger`
        Logging object.
    nersc : :class:`str`
        Holds the value of :envvar:`NERSC_HOST`, or ``None`` if not defined.
    options : :class:`argparse.Namespace`
        The parsed command-line options.
    product_url : :class:`str`
        The URL that will be used to download the code.  This differs from
        `fullproduct` in that it includes the tag or branch name.
    """
    default_nersc_dir_template = '/global/common/software/desi/{nersc_host}/desiconda/{desiconda_version}'

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
                     'USER': None,
                     'LANG': None,
                     'DESICONDA': None,
                     'NERSC_HOST': None}
        for e in check_env:
            try:
                check_env[e] = os.environ[e]
            except KeyError:
                self.log.warning('The environment variable %s is not set!',
                                 e)
        parser = ArgumentParser(description="Install DESI software.",
                                prog=os.path.basename(sys.argv[0]))
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
        parser.add_argument('-p', '--additional-products', action='append',
                            dest='additional',
                            metavar='PRODUCT:URL',
                            help=("Add or override known products " +
                                  "(e.g. new_product:https://github.com/mystuff/new_product)."))
        parser.add_argument('-r', '--root', action='store',
                            dest='root',
                            metavar='DIR',
                            help=('Override the root install directory.' +
                                  '(e.g. if installing into $SCRATCH).'))
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
        parser.add_argument('-W', '--no-world', action='store_false',
                            dest='world',
                            help='Disable world-readable installation.')
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
                not os.path.isdir(self.options.moduleshome)):
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
        if self.options.additional is not None:
            for k in self.options.additional:
                a = k.split(':', 1)
                known_products[a[0]] = a[1]
        if '/' in self.options.product:
            self.baseproduct = os.path.basename(self.options.product)
        else:
            self.baseproduct = self.options.product
        try:
            self.fullproduct = known_products[self.baseproduct]
        except KeyError:
            self.fullproduct = f'https://github.com/desihub/{self.baseproduct}'
            self.log.warning('Guessing %s is at %s.',
                             self.baseproduct, self.fullproduct)
            self.log.warning('Add location to desiutil.install.known_products ' +
                             'if that is incorrect.')
        self.baseversion = os.path.basename(self.options.product_version)
        self.github = False
        if 'github.com' in self.fullproduct:
            self.github = True
            self.log.debug("Detected GitHub install.")
        return (self.fullproduct, self.baseproduct, self.baseversion)

    def identify_branch(self):
        """If this is not a tag install, determine the branch identity.

        Returns
        -------
        :class:`str`
            The full path to the branch code.
        """
        self.is_branch = (self.options.product_version.startswith('branches') or
                          self.options.product_version == 'trunk' or
                          self.options.product_version == 'main')
        if self.is_branch:
            if self.github:
                self.product_url = self.fullproduct + '.git'
            else:
                if self.options.product_version == 'branches/trunk':
                    self.product_url = os.path.join(self.fullproduct, 'trunk')
                else:
                    self.product_url = os.path.join(self.fullproduct,
                                                    self.options.product_version)
        else:
            if self.github:
                self.product_url = os.path.join(self.fullproduct, 'archive',
                                                self.options.product_version +
                                                '.tar.gz')
            else:
                self.product_url = os.path.join(self.fullproduct, 'tags',
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
        self.working_dir = os.path.join(os.path.abspath('.'),
                                        '{0}-{1}'.format(self.baseproduct,
                                                         self.baseversion))
        if os.path.isdir(self.working_dir):
            self.log.info("Detected old working directory, %s. Deleting...",
                          self.working_dir)
            self.log.debug("shutil.rmtree('%s')", self.working_dir)
            if not self.options.test:
                shutil.rmtree(self.working_dir)
        if self.github:
            if self.is_branch:
                try:
                    r = requests.get(os.path.join(self.fullproduct, 'tree',
                                                  self.baseversion))
                    r.raise_for_status()
                except requests.exceptions.HTTPError:
                    message = f"Branch {self.baseversion} does not appear to exist. HTTP response was {r.status_code:d}."
                    self.log.critical(message)
                    raise DesiInstallException(message)
                command = ['git', 'clone', '-q', '-b', self.baseversion,
                           self.product_url, self.working_dir]
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
                # if self.is_branch:
                #     original_dir = os.getcwd()
                #     self.log.debug("os.chdir('%s')", self.working_dir)
                #     if not self.options.test:
                #         os.chdir(self.working_dir)
                #     command = ['git', 'checkout', '-q', '-b', self.baseversion,
                #                'origin/'+self.baseversion]
                #     self.log.debug(' '.join(command))
                #     if self.options.test:
                #         out, err = 'Test Mode.', ''
                #     else:
                #         proc = Popen(command, universal_newlines=True,
                #                      stdout=PIPE, stderr=PIPE)
                #         out, err = proc.communicate()
                #     self.log.debug(out)
                #     if len(err) > 0:
                #         message = ("git error while changing branch:" +
                #                    " {0}".format(err))
                #         self.log.critical(message)
                #         raise DesiInstallException(message)
                #     self.log.debug("os.chdir('%s')", original_dir)
                #     if not self.options.test:
                #         os.chdir(original_dir)
            else:
                if self.options.test:
                    self.log.debug("Test Mode. Skipping download of %s.",
                                   self.product_url)
                else:
                    try:
                        r = requests.get(self.product_url)
                        r.raise_for_status()
                    except requests.exceptions.HTTPError:
                        message = f"Error while downloading {self.product_url}, HTTP response was {r.status_code:d}."
                        self.log.critical(message)
                        raise DesiInstallException(message)
                    try:
                        tgz = BytesIO(r.content)
                        tf = tarfile.open(fileobj=tgz, mode='r:gz')
                        tf.extractall()
                        tf.close()
                        tgz.close()
                        self.working_dir = os.path.join(os.path.abspath('.'),
                                                        '{0}-{1}'.format(self.baseproduct,
                                                                         self.baseversion))
                        if self.baseversion.startswith('v'):
                            nov = os.path.join(os.path.abspath('.'),
                                               '{0}-{1}'.format(self.baseproduct,
                                                                self.baseversion[1:]))
                            if os.path.exists(nov):
                                self.working_dir = nov
                    except tarfile.TarError as e:
                        message = "tar error while expanding product code!"
                        self.log.critical(message)
                        raise DesiInstallException(message)
        else:
            if self.is_branch:
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
            if (os.path.exists(os.path.join(self.working_dir, 'pyproject.toml')) or os.path.exists(os.path.join(self.working_dir, 'setup.py'))):
                self.log.debug("Detected build type: py")
                build_type.add('py')
            elif os.path.exists(os.path.join(self.working_dir, 'Makefile')):
                self.log.debug("Detected build type: make")
                build_type.add('make')
            else:
                if os.path.isdir(os.path.join(self.working_dir, 'src')):
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
            desiconda = os.path.normpath(os.environ['DESICONDA'])
        except KeyError:
            return 'current'
        try:
            return os.path.basename(desiconda[:desiconda.index('/conda')])
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
            return self.default_nersc_dir_template.format(nersc_host=self.nersc,
                                                          desiconda_version=self.options.anaconda)
        return self.default_nersc_dir_template.format(nersc_host=nersc_host,
                                                      desiconda_version=self.options.anaconda)

    def set_install_dir(self):
        """Decide on an install directory.

        Returns
        -------
        :class:`str`
            The directory selected for installation.
        """
        try:
            self.nersc = os.environ['NERSC_HOST']
        except KeyError:
            self.nersc = None
        if self.options.root is None and self.nersc is not None:
            self.options.root = self.default_nersc_dir()

        if ((self.options.root is None or not os.path.isdir(self.options.root)) and not self.options.test):
            message = "Root install directory is missing or not set."
            self.log.critical(message)
            raise DesiInstallException(message)

        self.install_dir = os.path.join(self.options.root, 'code',
                                        self.baseproduct, self.baseversion)
        if os.path.isdir(self.install_dir) and not self.options.test:
            if self.options.force:
                self.unlock_permissions()
                self.log.debug("shutil.rmtree('%s')", self.install_dir)
                if not self.options.test:
                    shutil.rmtree(self.install_dir)
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
        self.module_file = os.path.join(self.working_dir, 'etc',
                                        self.baseproduct + '.module')
        if not os.path.exists(self.module_file):
            self.module_file = str(files('desiutil') / 'data' / 'desiutil.module')
        if self.options.test:
            self.log.debug('Test Mode. Skipping loading of dependencies.')
            self.deps = list()
        else:
            self.deps = dependencies(self.module_file)
            for d in self.deps:
                base_d = d.split('/')[0]
                if base_d in os.environ['LOADEDMODULES']:
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
        if hasattr(self, 'options'):
            if self.options.root is not None:
                return os.path.join(self.options.root, 'modulefiles')
        if not hasattr(self, 'nersc'):
            return None
        if self.nersc is None:
            return None
        else:
            return os.path.join(self.default_nersc_dir(), 'modulefiles')

    def install_module(self):
        """Process the module file.

        Returns
        -------
        :class:`str`
            The text of the processed module file.
        """
        dev = False
        if 'py' in self.build_type:
            if self.is_branch:
                dev = True
        else:
            if os.path.isdir(os.path.join(self.working_dir, 'py')):
                dev = True
        self.log.debug("configure_module(%s, %s, working_dir=%s, dev=%s)",
                       self.baseproduct, self.baseversion,
                       self.working_dir, dev)
        self.module_keywords = configure_module(self.baseproduct,
                                                self.baseversion,
                                                os.path.join(self.options.root, 'code'),
                                                working_dir=self.working_dir,
                                                dev=dev)
        if self.nersc is None:
            module_directory = os.path.join(self.options.root, 'modulefiles')
        else:
            module_directory = self.nersc_module_dir
        #
        # process_module() will handle the creation of the module directory.
        #
        if self.options.test:
            self.log.debug("Test Mode. Skipping Module file installation.")
            mod = ''
        else:
            try:
                self.log.debug(("process_module('%s', self.module_keywords, " +
                                "'%s')"), self.module_file,
                               module_directory)
                mod = process_module(self.module_file, self.module_keywords,
                                     module_directory)
                # Remove write permission to avoid accidental changes
                outfile = os.path.join(module_directory,
                                       self.module_keywords['name'],
                                       self.module_keywords['version'])
            except OSError as ose:
                self.log.critical(ose.strerror)
                raise DesiInstallException(ose.strerror)
            if self.options.default:
                self.log.debug("default_module(self.module_keywords, '%s')",
                               module_directory)
                dot_version = default_module(self.module_keywords,
                                             module_directory)

        return mod

    def prepare_environment(self):
        """Prepare the environment for the install.

        Returns
        -------
        :class:`str`
            The current working directory.  Because we're about to change it.
        """
        os.environ['WORKING_DIR'] = self.working_dir
        os.environ['INSTALL_DIR'] = self.install_dir
        if self.baseproduct == 'desiutil':
            os.environ['DESIUTIL'] = self.install_dir
        else:
            if self.baseproduct in os.environ['LOADEDMODULES']:
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
        if env_version not in os.environ:
            os.environ[env_version] = 'tags/'+self.baseversion
        self.original_dir = os.getcwd()
        return self.original_dir

    def install(self):
        """Run setup.py, etc.
        """
        if (self.build_type == set(['plain']) or self.is_branch):
            #
            # For certain installs, all that is needed is to copy the
            # downloaded code to the install directory.
            #
            self.log.debug("shutil.copytree('%s', '%s')",
                           self.working_dir, self.install_dir)
            if self.options.test:
                self.log.debug("Test mode. Skipping copy of %s to %s.",
                               self.working_dir, self.install_dir)
            else:
                shutil.copytree(self.working_dir, self.install_dir)
        else:
            #
            # Run a 'real' install
            #
            # os.chdir(self.working_dir)
            if 'py' in self.build_type:
                #
                # For Python installs, a site-packages directory needs to
                # exist.  We may need to manipulate sys.path to include this
                # directory.
                #
                lib_dir = os.path.join(self.install_dir, 'lib',
                                       self.module_keywords['pyversion'],
                                       'site-packages')
                if self.options.test:
                    self.log.debug("Test Mode.  Skipping creation of %s.",
                                   lib_dir)
                else:
                    self.log.debug("os.makedirs('%s')", lib_dir)
                    try:
                        os.makedirs(lib_dir)
                    except OSError as ose:
                        self.log.critical(ose.strerror)
                        raise DesiInstallException(ose.strerror)
                    if lib_dir not in sys.path:
                        try:
                            newpythonpath = (lib_dir + ':' +
                                             os.environ['PYTHONPATH'])
                        except KeyError:
                            newpythonpath = lib_dir
                        os.environ['PYTHONPATH'] = newpythonpath
                        sys.path.insert(int(sys.path[0] == ''), lib_dir)
                #
                # Ready to python setup.py
                #
                # command = [sys.executable, 'setup.py', 'install',
                #            '--prefix={0}'.format(self.install_dir)]
                command = [sys.executable, '-m', 'pip', 'install', '--no-deps',
                           '--disable-pip-version-check', '--ignore-installed',
                           '--no-warn-script-location',
                           '--prefix={0}'.format(self.install_dir), '.']
                self.log.debug(' '.join(command))
                if self.options.test:
                    # self.log.debug("Test Mode.  Skipping 'python setup.py install'.")
                    self.log.debug("Test Mode. Skipping 'pip install'.")
                else:
                    os.chdir(self.working_dir)
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    self.log.debug(out)
                    if len(err) > 0:
                        #
                        # Pass STDERR messages to the user, but do not
                        # raise an error unless the return code was non-zero.
                        #
                        if proc.returncode == 0:
                            message = ("Pip emitted messages on STDERR; these can probably be ignored:\n" +
                                       err)
                            self.log.warning(message)
                        else:
                            message = ("Potentially serious error detected during pip installation:\n" +
                                       err)
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
                    command = ['make', '-j', '8', 'install']
                self.log.debug(' '.join(command))
                if self.options.test:
                    self.log.debug("Test Mode.  Skipping 'make install'.")
                else:
                    if 'src' in self.build_type:
                        os.chdir(self.install_dir)
                    else:
                        os.chdir(self.working_dir)
                    proc = Popen(command, universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    self.log.debug(out)
                    if len(err) > 0:
                        #
                        # Pass STDERR messages to the user, but do not
                        # raise an error unless the return code was non-zero.
                        #
                        if proc.returncode == 0:
                            message = ("Make emitted messages on STDERR; these can probably be ignored:\n" +
                                       err)
                            self.log.warning(message)
                        else:
                            message = ("Potentially serious error detected during compile:\n" +
                                       err)
                            self.log.critical(message)
                            raise DesiInstallException(message)
        return

    def get_extra(self):
        """Download any additional data not included in the code repository.

        This is done here so that :envvar:`INSTALL_DIR` is defined *and*
        exists.
        """
        extra_script = os.path.join(self.working_dir, 'etc',
                                    '{0}_data.sh'.format(self.baseproduct))
        if os.path.exists(extra_script):
            self.log.debug("Detected extra script: %s.", extra_script)
            if self.options.test:
                self.log.debug('Test Mode. Skipping install of extra data.')
            else:
                proc = Popen([extra_script], universal_newlines=True,
                             stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                status = proc.returncode
                self.log.debug(out)
                if status != 0 and len(err) > 0:
                    message = "Error grabbing extra data: {0}".format(err)
                    self.log.critical(message)
                    raise DesiInstallException(message)
        return

    def compile_branch(self):
        """Certain packages need C/C++ code compiled even for a branch install.
        """
        if self.is_branch:
            compile_script = os.path.join(self.install_dir, 'etc',
                                          '{0}_compile.sh'.format(self.baseproduct))
            if os.path.exists(compile_script):
                self.log.debug("Detected compile script: %s.", compile_script)
                if self.options.test:
                    self.log.debug('Test Mode. Skipping compile script.')
                else:
                    current_dir = os.getcwd()
                    self.log.debug("os.chdir('%s')", self.install_dir)
                    os.chdir(self.install_dir)
                    proc = Popen([compile_script, sys.executable], universal_newlines=True,
                                 stdout=PIPE, stderr=PIPE)
                    out, err = proc.communicate()
                    status = proc.returncode
                    self.log.debug(out)
                    self.log.debug("os.chdir('%s')", current_dir)
                    os.chdir(current_dir)
                    if status != 0 and len(err) > 0:
                        message = "Error compiling code: {0}".format(err)
                        self.log.critical(message)
                        raise DesiInstallException(message)
        return

    def verify_bootstrap(self):
        """Make sure that desiutil/desiInstall was installed with
        an explicit Python executable path.

        For anything besides an initial bootstrap install of desiutil,
        this function does nothing.

        Returns
        -------
        :class:`bool`
            Returns ``True`` if everything is OK.
        """
        if self.options.bootstrap:
            desiInstall = os.path.join(self.install_dir, 'bin', 'desiInstall')
            with open(desiInstall, 'r') as d:
                lines = d.readlines()
            self.log.debug("%s", lines[0].strip())
            if self.options.anaconda not in lines[0]:
                message = ("desiInstall executable ({0}) does not contain " +
                           "an explicit desiconda version " +
                           "({1})!").format(desiInstall, self.options.anaconda)
                self.log.critical(message)
                raise DesiInstallException(message)
        return True

    def permissions(self):
        """Set permissions on installed software.
        """
        read_file = stat.S_IRUSR | stat.S_IRGRP
        if self.options.world:
            read_file |= stat.S_IROTH
        read_exec = read_file | stat.S_IXUSR | stat.S_IXGRP
        if self.options.world:
            read_exec |= stat.S_IXOTH
        read_dir = read_exec | stat.S_ISGID
        if self.is_branch:
            read_file |= stat.S_IWUSR
            read_exec |= stat.S_IWUSR
            read_dir |= stat.S_IWUSR
        #
        # Recursively set permissions from the bottom up.
        #
        for dirpath, dirnames, filenames in os.walk(self.install_dir, topdown=False):
            for f in filenames:
                fname = os.path.join(dirpath, f)
                if os.path.islink(fname):
                    continue
                executable = (stat.S_IMODE(os.stat(fname).st_mode) & stat.S_IXUSR) != 0
                if executable:
                    self.log.debug("os.chmod('%s', %s)", fname, read_exec)
                    os.chmod(fname, read_exec)
                else:
                    self.log.debug("os.chmod('%s', %s)", fname, read_exec)
                    os.chmod(fname, read_file)
            for d in dirnames:
                self.log.debug("os.chmod('%s', %s)", os.path.join(dirpath, d), read_dir)
                os.chmod(os.path.join(dirpath, d), read_dir)
        #
        # Finally set permissions on the top directory.
        #
        self.log.debug("os.chmod('%s', %s)", self.install_dir, read_dir)
        os.chmod(self.install_dir, read_dir)

    def unlock_permissions(self):
        """Unlock installed directories to allow their removal.

        Returns
        -------
        :class:`int`
            Status code returned by :command:`chmod`.
        """
        command = ['chmod', '-R', 'u+w', self.install_dir]
        self.log.debug(' '.join(command))
        proc = Popen(command, universal_newlines=True,
                     stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        self.log.debug(out)
        return proc.returncode

    def cleanup(self):
        """Clean up after the install.

        Returns
        -------
        :class:`bool`
            Returns ``True``
        """
        self.log.debug("os.chdir('%s')", self.original_dir)
        if not self.options.test:
            os.chdir(self.original_dir)
        if not self.options.keep:
            self.log.debug("shutil.rmtree('%s')", self.working_dir)
            if not self.options.test:
                shutil.rmtree(self.working_dir)
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
            self.set_install_dir()
            self.start_modules()
            self.module_dependencies()
            self.install_module()
            self.prepare_environment()
            self.install()
            self.get_extra()
            self.compile_branch()
            self.verify_bootstrap()
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
