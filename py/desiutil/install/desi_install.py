# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Install DESI software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
import logging
import subprocess
import requests
from logging.handlers import MemoryHandler
from datetime import date
from os import chdir, environ, getcwd, makedirs, remove, symlink
from os.path import abspath, basename, exists, isdir, join
from shutil import copyfile, copytree, rmtree
from sys import argv, executable, path, version_info
from .dependencies import dependencies
from .known_products import known_products
from ..git import last_tag
from .. import __version__ as desiUtilVersion
#
#
#
class DesiInstallException(Exception):
    """The methods of :class:`DesiInstall` should raise this exception
    to indicate that the command-line script should exit immediately.
    """
    pass
#
#
#
class DesiInstall(object):
    """Code and data that drive the desiInstall script.

    Parameters
    ----------
    test : bool, optional
        If ``True`` log messages will be supressed for testing purposes.

    Attributes
    ----------
    baseproduct : str
        The bare name of the product, *e.g.* "desiutil".
    baseversion : str
        The bare version, without any ``branches/`` qualifiers.
    debug : bool
        ``True`` if the ``--test`` or ``--verbose`` options were selected.
    executable : str
        The command used to invoke the script.
    fullproduct : str
        The path to the product relative to its URL, *e.g.*, "desihub/desiutil".
    github : bool
        ``True`` if the selected product lives on GitHub.
    is_branch : bool
        ``True`` if a branch has been selected.
    is_trunk : bool
        ``True`` if trunk or the master branch has been selected.
    ll : int
        The log level.
    options : argparse.Namespace
        The parsed command-line options.
    product_url : str
        The URL that will be used to download the code.
    test : bool
        Captures the value of the test argument passed to the constructor.
    """
    #
    #
    #
    def __init__(self,test=False):
        """Bare-bones initialization.  The only thing done here is setting up
        the logging infrastructure.
        """
        self.executable = basename(argv[0])
        self.test = test
        if self.test:
            nh = logging.NullHandler()
            mh = MemoryHandler(1000000,flushLevel=logging.CRITICAL,target=nh)
            logging.getLogger(__name__).addHandler(mh)
        else: # pragma: no cover
            logging.basicConfig(format=self.executable+' [%(name)s] Log - %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
        return
    #
    #
    #
    def get_options(self,test_args=None):
        """Parse command-line arguments passed to the desiInstall script.

        Parameters
        ----------
        test_args : list
            Normally, this method is called without arguments, and ``sys.argv``
            is parsed.  Arguments should only be passed for testing purposes.

        Returns
        -------
        get_options : argparse.Namespace
            A simple object containing the parsed options.  Also, the
            attribute `options` is set.
        """
        from argparse import ArgumentParser
        log = logging.getLogger(__name__+'.DesiInstall.get_options')
        check_env = {'MODULESHOME':None,'DESI_PRODUCT_ROOT':None,'USER':None}
        for e in check_env:
            try:
                check_env[e] = environ[e]
            except KeyError:
                log.warning('The environment variable {0} is not set!'.format(e))
        parser = ArgumentParser(description="Install DESI software.",prog=self.executable)
        parser.add_argument('-b', '--bootstrap', action='store_true', dest='bootstrap',
            help="Run in bootstrap mode to install the desiutil product.")
        parser.add_argument('-C', '--compile-c', action='store_true', dest='force_build_type',
            help="Force C/C++ install mode, even if a setup.py file is detected (WARNING: this is for experts only).")
        parser.add_argument('-d', '--default', action='store_true', dest='default',
            help='Make this version the default version.')
        parser.add_argument('-D', '--no-documentation', action='store_false', dest='documentation',
            help='Do NOT build any Sphinx or Doxygen documentation.')
        parser.add_argument('-F', '--force', action='store_true', dest='force',
            help='Overwrite any existing installation of this product/version.')
        parser.add_argument('-k', '--keep', action='store_true', dest='keep',
            help='Keep the exported build directory.')
        parser.add_argument('-m', '--module-home', action='store', dest='moduleshome',
            metavar='DIR',help='Set or override the value of $MODULESHOME',
            default=check_env['MODULESHOME'])
        parser.add_argument('-M', '--module-dir', action='store', dest='moduledir',
            metavar='DIR',help="Install module files in DIR.",default='')
        parser.add_argument('-p', '--python', action='store', dest='python',
            metavar='PYTHON',help="Use the Python executable PYTHON (e.g. /opt/local/bin/python2.7).  This option is only relevant when installing desiutil itself.")
        parser.add_argument('-r', '--root', action='store', dest='root',
            metavar='DIR', help='Set or override the value of $DESI_PRODUCT_ROOT',
            default=check_env['DESI_PRODUCT_ROOT'])
        parser.add_argument('-t', '--test', action='store_true', dest='test',
            help='Test mode.  Do not actually install anything.')
        parser.add_argument('-u', '--url', action='store',dest='url',
            metavar='URL',help="Download software from URL.",
            default='https://desi.lbl.gov/svn/code')
        parser.add_argument('-U', '--username', action='store', dest='username',
            metavar='USER',help="Set svn username to USER.",default=check_env['USER'])
        parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
            help='Print extra information.')
        parser.add_argument('-V', '--version', action='version',
            version='%(prog)s '+desiUtilVersion)
        parser.add_argument('-x', '--cross-install', action='store_true', dest='cross_install',
            help='Make the install available on multiple systems (e.g. NERSC).')
        parser.add_argument('product',nargs='?',default='NO PACKAGE',
            help='Name of product to install.')
        parser.add_argument('product_version',nargs='?',default='NO VERSION',
            help='Version of product to install.')
        if test_args is None: # pragma: no cover
            self.options = parser.parse_args()
        else:
            self.options = parser.parse_args(test_args)
        self.debug = self.options.verbose or self.options.test
        self.ll = logging.INFO
        if self.debug:
            self.ll = logging.DEBUG
        logging.getLogger(__name__).setLevel(self.ll)
        if test_args is not None:
            log.debug('Called parse_args() with: {0}'.format(' '.join(test_args)))
        log.debug('Set log level to {0}.'.format(logging.getLevelName(self.ll)))
        return self.options
    #
    #
    #
    def sanity_check(self):
        """Sanity check the options.

        Parameters
        ----------
        None

        Returns
        -------
        sanity_check : bool
            ``True`` if there were no problems.

        Raises
        ------
        DesiInstallException
            If any options don't make sense.
        """
        log = logging.getLogger(__name__+'.DesiInstall.sanity_check')
        if self.options.product == 'NO PACKAGE' or self.options.product_version == 'NO VERSION':
            if self.options.bootstrap:
                self.options.default = True
                self.options.product = 'desihub/desiutil'
                self.options.product_version = last_tag('desihub','desiutil')
                log.info("Selected desiutil/{0} for installation.".format(self.options.product_version))
            else:
                message = "You must specify a product and a version!"
                log.critical(message)
                raise DesiInstallException(message)
        if self.options.moduleshome is None or not isdir(self.options.moduleshome):
            message = "You do not appear to have Modules set up."
            log.critical(message)
            raise DesiInstallException(message)
        return True
    #
    #
    #
    def get_product_version(self):
        """Determine the base product and version information.

        Parameters
        ----------
        None

        Returns
        -------
        get_product_version : tuple
            A tuple containing the base product name and version.

        Raises
        ------
        DesiInstallException
            If the product and version inputs didn't make sense.
        """
        log = logging.getLogger(__name__+'.DesiInstall.get_product_version')
        if '/' in self.options.product:
            self.fullproduct = self.options.product
            self.baseproduct = basename(self.options.product)
        else:
            try:
                self.fullproduct = known_products[self.options.product]
                self.baseproduct = self.options.product
            except KeyError:
                message = "Could not determine the exact location of {0}!".format(self.options.product)
                log.critical(message)
                raise DesiInstallException(message)
        self.baseversion = basename(self.options.product_version)
        self.github = False
        if self.fullproduct.startswith('desihub/'):
            self.github = True
            self.options.url = 'https://github.com'
            log.debug("Detected GitHub install.")
        return (self.fullproduct, self.baseproduct, self.baseversion)
    #
    #
    #
    def identify_branch(self):
        """If this is not a tag install, determine whether this is a trunk or branch install.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        log = logging.getLogger(__name__+'.DesiInstall.identify_branch')
        self.is_branch = self.options.product_version.startswith('branches')
        self.is_trunk = self.options.product_version == 'trunk' or self.options.product_version == 'master'
        if self.is_trunk or self.is_branch:
            if self.github:
                self.product_url = join(self.options.url,self.fullproduct)+'.git'
            else:
                self.product_url = join(self.options.url,self.fullproduct,self.options.product_version)
        else:
            if self.github:
                self.product_url = join(self.options.url,self.fullproduct,'archive',self.options.product_version+'.tar.gz')
            else:
                self.product_url = join(self.options.url,self.fullproduct,'tags',self.options.product_version)
        log.debug("Using {0} as the URL of this product.".format(self.product_url))
        return self.product_url
    #
    #
    #
    def verify_url(self):
        """Ensure that the download URL is valid.
        """
        log = logging.getLogger(__name__+'.DesiInstall.verify_url')
        if not self.github:
            command = ['svn','--non-interactive','--username',self.options.username,'ls',self.product_url]
            log.debug(' '.join(command))
            proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = proc.communicate()
            log.debug(out)
            if len(err) > 0:
                message = "svn error while testing product URL: {0}".format(err)
                log.critical(message)
                raise DesiInstallException(message)
        return
    #
    #
    #
    def get_code(self):
        """Actually download the code.
        """
        log = logging.getLogger(__name__+'.DesiInstall.get_code')
        self.working_dir = join(abspath('.'),'{0}-{1}'.format(self.baseproduct,self.baseversion))
        if isdir(self.working_dir):
            log.info("Detected old working directory, {0}. Deleting...".format(self.working_dir))
            rmtree(self.working_dir)
        if self.github:
            if self.is_trunk or self.is_branch:
                if self.is_branch:
                    r = requests.get(join(self.options.url,self.fullproduct,'tree',self.baseversion))
                    if r.status_code != 200:
                        message = "Branch {0} does not appear to exist. HTTP response was {1:d}.".format(self.baseversion,r.status_code)
                        log.critical(message)
                        raise DesiInstallException(message)
                command = ['git', 'clone', '-q', self.product_url, self.working_dir]
                log.debug(' '.join(command))
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                log.debug(out)
                if len(err) > 0:
                    message = "git error while downloading product code: {0}".format(err)
                    log.critical(message)
                    raise DesiInstallException(message)
                if self.is_branch:
                    original_dir = getcwd()
                    chdir(self.working_dir)
                    command = ['git', 'checkout', '-q', '-b', self.baseversion, 'origin/'+self.baseversion]
                    log.debug(' '.join(command))
                    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    out, err = proc.communicate()
                    log.debug(out)
                    if len(err) > 0:
                        message = "git error while changing branch: {0}".format(err)
                        log.critical(message)
                        raise DesiInstallException(message)
                    chdir(original_dir)
            else:
                r = requests.get(self.product_url)
                if r.status_code != 200:
                    message = "Error while downloading {0}, HTTP response was {1:d}.".format(self.product_url,r.status_code)
                    log.critical(message)
                    raise DesiInstallException(message)
                tgz = r.content
                with open(self.options.product_version+'.tar.gz','w') as u:
                    u.write(tgz)
                command = ['tar', '-xzf', self.options.product_version+'.tar.gz']
                log.debug(' '.join(command))
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                log.debug(out)
                if len(err) > 0:
                    message = "tar error while expanding product code: {0}".format(err)
                    log.critical(message)
                    raise DesiInstallException(message)
                log.debug("remove('{0}')".format(self.options.product_version+'.tar.gz'))
                remove(self.options.product_version+'.tar.gz')
        else:
            if self.is_trunk or self.is_branch:
                get_svn = 'checkout'
            else:
                get_svn = 'export'
            command = ['svn','--non-interactive','--username',self.options.username,get_svn,self.product_url,self.working_dir]
            log.debug(' '.join(command))
            proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = proc.communicate()
            log.debug(out)
            if len(err) > 0:
                message = "svn error while downloading product code: {0}".format(err)
                log.critical(message)
                raise DesiInstallException(message)
        return
    #
    #
    #
    def set_build_type(self):
        """Determine the build type.

        Parameters
        ----------
        force : bool, optional
            Set to ``True`` to force the 'make' build type.

        Returns
        -------
        set_build_type : set
            A set containing the detected build types.
        """
        log = logging.getLogger(__name__+'.DesiInstall.set_build_type')
        self.build_type = set(['plain'])
        if self.options.force_build_type:
            self.build_type.add('make')
        else:
            if exists(join(self.working_dir,'setup.py')):
                self.build_type.add('py')
            if exists(join(self.working_dir,'Makefile')):
                self.build_type.add('make')
            else:
                if isdir(join(self.working_dir,'src')):
                    self.build_type.add('src')
        return self.build_type
    #
    #
    #
    def set_install_dir(self):
        """Decide on an install directory.
        """
        log = logging.getLogger(__name__+'.DesiInstall.set_install_dir')
        self.nersc = None
        try:
            self.nersc = environ['NERSC_HOST']
        except KeyError:
            pass
        if self.options.root is None or not isdir(self.options.root):
            if self.nersc is not None:
                self.options.root = join('/project/projectdirs/desi/software',self.nersc)
            else:
                message = "DESI_PRODUCT_ROOT is missing or not set."
                log.critical(message)
                raise DesiInstallException(message)
        if self.options.root is not None:
            environ['DESI_PRODUCT_ROOT'] = self.options.root
        self.install_dir = join(self.options.root,self.baseproduct,self.baseversion)
        if isdir(self.install_dir) and not self.options.test:
            if self.options.force:
                rmtree(self.install_dir)
            else:
                message = "Install directory, {0}, already exists!".format(self.install_dir)
                log.critical(message)
                raise DesiInstallException(message)
        return
    #
    #
    #
    def init_modules(self):
        """Set up the modules infrastructure.
        """
        log = logging.getLogger(__name__+'.DesiInstall.init_modules')
        initpy_found = False
        for modpy in ('python','python.py'):
            initpy = join(self.options.moduleshome,'init',modpy)
            if exists(initpy):
                initpy_found = True
                execfile(initpy,globals())
                self.module = staticmethod(module)
        if not initpy_found:
            message = "Could not find the Python file in {0}/init!".format(options.moduleshome)
            log.critical(message)
            raise DesiInstallException(message)
        return
    #
    #
    #
    def module_dependencies(self):
        """Figure out the dependencies and load them.
        """
        log = logging.getLogger(__name__+'.DesiInstall.module_dependencies')
        self.module_file = join(self.working_dir,'etc',self.baseproduct+'.module')
        if not exists(self.module_file):
            self.module_file = join(environ['DESIUTIL'],'etc','desiutil.module')
        self.deps = dependencies(self.module_file)
        for d in self.deps:
            base_d = d.split('/')[0]
            if base_d in environ['LOADEDMODULES']:
                m_command = 'switch'
            else:
                m_command = 'load'
            log.debug("module('{0}','{1}')".format(m_command, d))
            self.module(m_command,d)
        return
    #
    #
    #
    def configure_module(self):
        """Decide what needs to go in the module file.
        """
        self.module_keywords = {
            'name': self.baseproduct,
            'version': self.baseversion,
            'needs_bin': '# ',
            'needs_python': '# ',
            'needs_trunk_py': '# ',
            'needs_ld_lib': '# ',
            'needs_idl': '# ',
            'pyversion': "python{0:d}.{1:d}".format(*version_info)
            }
        if isdir(join(self.working_dir,'bin')):
            self.module_keywords['needs_bin'] = ''
        if isdir(join(self.working_dir,'lib')):
            self.module_keywords['needs_ld_lib'] = ''
        if isdir(join(self.working_dir,'pro')):
            self.module_keywords['needs_idl'] = ''
        if 'py' in self.build_type:
            if self.is_branch or self.is_trunk:
                self.module_keywords['needs_trunk_py'] = ''
            else:
                self.module_keywords['needs_python'] = ''
        else:
            if isdir(join(self.working_dir,'py')):
                self.module_keywords['needs_trunk_py'] = ''
        return self.module_keywords
    #
    #
    #
    def process_module(self):
        """Process the module file.
        """
        log = logging.getLogger(__name__+'.DesiInstall.process_module')
        if exists(self.module_file):
            if self.options.moduledir == '':
                #
                # We didn't set a module dir, so derive it from options.root
                #
                if self.nersc is None:
                    self.options.moduledir = join(self.options.root,'modulefiles')
                else:
                    self.options.moduledir = join('/project/projectdirs/desi/software/modules',self.nersc)
                if not self.options.test:
                    if not isdir(self.options.moduledir):
                        log.info("Creating Modules directory {0}.".format(self.options.moduledir))
                        try:
                            makedirs(self.options.moduledir)
                        except OSError as ose:
                            log.critical(ose.strerror)
                            raise DesiInstallException(ose.strerror)
            if not self.options.test:
                if not isdir(join(self.options.moduledir,self.baseproduct)):
                    try:
                        makedirs(join(self.options.moduledir,self.baseproduct))
                    except OSError as ose:
                        log.critical(ose.strerror)
                        raise DesiInstallException(ose.strerror)
            install_module_file = join(self.options.moduledir,self.baseproduct,self.baseversion)
            with open(self.module_file) as m:
                mod = m.read().format(**self.module_keywords)
            if self.options.test:
                log.debug(mod)
            else:
                with open(install_module_file,'w') as m:
                    m.write(mod)
                if self.options.default:
                    dot_version = '#%Module1.0\nset ModulesVersion "{0}"\n'.format(self.baseversion)
                    install_version_file = join(self.options.moduledir,self.baseproduct,'.version')
                    with open(install_version_file,'w') as v:
                        v.write(dot_version)
        return
    #
    #
    #
    def prepare_environment(self):
        """Prepare the environment for the install.
        """
        log = logging.getLogger(__name__+'.DesiInstall.prepare_environment')
        environ['WORKING_DIR'] = self.working_dir
        environ['INSTALL_DIR'] = self.install_dir
        if baseproduct == 'desiutil':
            environ['DESIUTIL'] = self.install_dir
        else:
            if self.baseproduct in environ['LOADEDMODULES']:
                m_command = 'switch'
            else:
                m_command = 'load'
            log.debug("module('{0}','{1}/{2}')".format(m_command,baseproduct,baseversion))
            self.module(m_command,self.baseproduct+'/'+self.baseversion)
        self.original_dir = getcwd()
        return
    #
    #
    #
    def copy_install(self):
        """Simply copying the files from the checkout to the install.
        """
        log = logging.getLogger(__name__+'.DesiInstall.copy_install')
        log.debug("copytree('{0}','{1}')".format(self.working_dir,self.install_dir))
        if not self.options.test:
            copytree(self.working_dir,self.install_dir)
        return
    #
    #
    #
    def install(self):
        """Run setup.py, etc.
        """
        log = logging.getLogger(__name__+'.DesiInstall.install')
        if (self.is_trunk or self.is_branch):
            if 'src' in self.build_type:
                chdir(self.install_dir)
                command = ['make','-C', 'src', 'all']
                log.info('Running "{0}" in {1}.'.format(' '.join(command),self.install_dir))
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                log.debug(out)
                if len(err) > 0:
                    message = "Error during compile: {0}".format(err)
                    log.critical(message)
                    raise DesiInstallException(message)
            if self.options.documentation:
                log.warning('Documentation will not be built automatically for trunk or branch installs!')
                log.warning('You can use the desiDoc script to build documentation on your own.')
        else:
            #
            # Run a 'real' install
            #
            chdir(self.working_dir)
            if 'py' in self.build_type:
                #
                # For Python installs, a site-packages directory needs to exist.
                # We may need to manipulate sys.path to include this directory.
                #
                lib_dir = join(self.install_dir,'lib',self.module_keywords['pyversion'],'site-packages')
                if not self.options.test:
                    try:
                        makedirs(lib_dir)
                    except OSError as ose:
                        log.critical(ose.strerror)
                        raise DesiInstallException(ose.strerror)
                    if lib_dir not in path:
                        try:
                            newpythonpath = lib_dir + ':' + environ['PYTHONPATH']
                        except KeyError:
                            newpythonpath = lib_dir
                        environ['PYTHONPATH'] = newpythonpath
                        path.insert(int(path[0] == ''),lib_dir)
                #
                # Ready to python setup.py
                #
                command = [executable, 'setup.py', 'install', '--prefix={0}'.format(self.install_dir)]
                log.debug(' '.join(command))
                if not self.options.test:
                    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    out, err = proc.communicate()
                    log.debug(out)
                    if len(err) > 0:
                        message = "Error during installation: {0}".format(err)
                        log.critical(message)
                        raise DesiInstallException(message)
            #
            # Build documentation
            #
            if self.options.documentation:
                self.generate_doc()
            #
            # At this point either we have already completed a Python installation
            # or we still need to compile the C/C++ product (we had to construct
            # doc/Makefile first).
            #
            if 'make' in self.build_type or 'src' in self.build_type:
                if 'src' in self.build_type:
                    chdir(self.install_dir)
                    command = ['make','-C', 'src', 'all']
                else:
                    command = ['make', 'install']
                log.debug(' '.join(command))
                if not self.options.test:
                    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    out, err = proc.communicate()
                    log.debug(out)
                    if len(err) > 0:
                        message = "Error during compile: {0}".format(err)
                        log.critical(message)
                        raise DesiInstallException(message)
            #
            # Link documentation into www directory at NERSC
            #
            if self.options.documentation:
                if self.nersc is None:
                    log.debug("Skipping installation into www directory.")
                else:
                    www_dir = join('/project/projectdirs/desi/www/doc',self.baseproduct)
                    if not isdir(www_dir):
                        makedirs(www_dir)
                    doc_dir = join(self.install_dir,'doc','html')
                    if islink(join(www_dir,self.baseversion)):
                        log.warning("Documentation for {0}/{1} already exists.".format(self.baseproduct,self.baseversion))
                    else:
                        if isdir(doc_dir):
                            log.debug("symlink('{0}','{1}')".format(doc_dir,join(www_dir,self.baseversion)))
                            symlink(doc_dir,join(www_dir,self.baseversion))
        return
    #
    #
    #
    def generate_doc(self):
        """Generate the documentation.
        """
        log = logging.getLogger(__name__+'.DesiInstall.generate_doc')
        if 'py' in self.build_type or isdir('py'):
            if exists(join('doc','index.rst')):
                #
                # Assume Sphinx documentation.
                #
                sphinx_dir = join(environ['DESIUTIL'],'etc','doc','sphinx')
                sphinx_keywords = {
                    'name':self.baseproduct,
                    'release':self.baseversion,
                    'version':'.'.join(self.baseversion.split('.')[0:3]),
                    'year':date.today().year}
                # for sd in ('_build','_static'):
                #     if not isdir(join('doc',sd)):
                #         try:
                #             makedirs(join('doc',sd))
                #         except OSError as ose:
                #             log.critical(ose.strerror)
                #             raise DesiInstallException(ose.strerror)
                if not exists(join('doc','Makefile')):
                    log.debug("copyfile('{0}','{1}')".format(join(sphinx_dir,'Makefile'),join('doc','Makefile')))
                    copyfile(join(sphinx_dir,'Makefile'),join('doc','Makefile'))
                if not exists(join('doc','conf.py')):
                    with open(join(sphinx_dir,'conf.py')) as conf:
                        newconf = conf.read().format(**sphinx_keywords)
                    with open(join('doc','conf.py'),'w') as conf2:
                        conf2.write(newconf)
                if not exists(join('doc','_templates')):
                    log.debug("copytree('{0}','{1}')".format(join(sphinx_dir,'_templates'),join('doc','_templates')))
                    copytree(join(sphinx_dir,'_templates'),join('doc','_templates'))
                command = [executable, 'setup.py', 'build_sphinx', '--fresh-env', '--all-files']
                log.debug(' '.join(command))
                if not options.test:
                    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    out, err = proc.communicate()
                    log.debug(out)
                    if len(err) > 0:
                        message = "Error during documentation build: {0}".format(err)
                        log.critical(message)
                        raise DesiInstallException(message)
                if not options.test and install_dir is not None:
                    if isdir(join('build','sphinx','html')):
                        log.debug("copytree('{0}','{1}')".format(join('build','sphinx','html'),join(install_dir,'doc','html','sphinx')))
                        copytree(join('build','sphinx','html'),join(install_dir,'doc','html','sphinx'))
            else:
                log.warning("Documentation build requested, but no documentation found.")
        #
        # Look for Doxygen documentation.
        #
        if 'make' in build_type:
            if isdir('doc'):
                doxygen_keywords = {
                    'name':baseproduct,
                    'version':baseversion,
                    'description':"Documentation for {0} built by desiInstall.".format(baseproduct)}
                if not exists(join('doc','Doxygen.Makefile')):
                    log.debug("copyfile('{0}','{1}')".format(
                        join(getenv('DESIUTIL'),'etc','doc','doxygen','Makefile'),
                        join('doc','Doxygen.Makefile')))
                    copyfile(join(getenv('DESIUTIL'),'etc','doc','doxygen','Makefile'),
                        join('doc','Doxygen.Makefile'))
                if not exists(join('doc','Doxyfile')):
                    with open(join(getenv('DESIUTIL'),'etc','doc','doxygen','Doxyfile')) as conf:
                        newconf = conf.read().format(**doxygen_keywords)
                    with open(join('doc','Doxyfile'),'w') as conf2:
                        conf2.write(newconf)
                command = ['make', '-C', 'doc', '-f', 'Doxygen.Makefile', 'all']
                log.debug(' '.join(command))
                if not options.test:
                    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    out, err = proc.communicate()
                    log.debug(out)
                    if len(err) > 0:
                        message = "Error during compile: {0}".format(err)
                        log.critical(message)
                        raise DesiInstallException(message)
            else:
                log.warning("Documentation build requested, but no documentation found.")
        return
    #
    #
    #
    def cross_install(self):
        """Make package available on multiple hosts.
        """
        cross_install_host = 'edison'
        log = logging.getLogger(__name__+'.DesiInstall.cross_install')
        if self.options.cross_install:
            if self.nersc is None:
                log.error("Cross-installs are only supported at NERSC.")
            elif self.nersc != cross_install_host:
                log.error("Cross-installs should be performed on edison.")
            else:
                for nh in ('carver','hopper','datatran','scigate'):
                    if not islink(join('/project/projectdirs/desi/software',nh,self.baseproduct)):
                        log.debug("symlink('../edison/{0}','/project/projectdirs/desi/software/{1}/{0}')".format(self.baseproduct,nh))
                        symlink(join('..',cross_install_host,self.baseproduct),join('/project/projectdirs/desi/software',nh,self.baseproduct))
                    if not islink(join('/project/projectdirs/desi/software/modules',nh,self.baseproduct)):
                        log.debug("symlink('../edison/{0}','/project/projectdirs/desi/software/modules/{1}/{0}')".format(self.baseproduct,nh))
                        symlink(join('..',cross_install_host,self.baseproduct),join('/project/projectdirs/desi/modules/software',nh,self.baseproduct))
        return
    #
    #
    #
    def cleanup(self):
        """Clean up after the install.
        """
        log = logging.getLogger(__name__+'.DesiInstall.cleanup')
        log.debug("chdir('{0}')".format(self.original_dir))
        chdir(self.original_dir)
        if not self.options.keep:
            log.debug("rmtree('{0}')".format(self.working_dir))
            rmtree(self.working_dir)
        return
    #
    #
    #
    def run(self): # pragma: no cover
        """This method wraps all the standard steps of the desiInstall script.

        Parameters
        ----------
        None

        Returns
        -------
        run : int
            An integer suitable for passing to sys.exit.
        """
        log = logging.getLogger(__name__+'.DesiInstall.run')
        log.debug('Commencing run().')
        self.get_options()
        try:
            self.sanity_check()
            fullproduct, baseproduct, baseversion = self.get_product_version()
            self.identify_branch()
            self.verify_url()
            self.get_code()
            build_type = self.set_build_type()
            self.set_install_dir()
            self.init_modules()
            self.module_dependencies()
            self.configure_module()
            self.process_module()
            self.copy_install()
            self.install()
            self.cross_install()
        except DesiInstallException:
            return 1
        self.cleanup()
        log.debug('run() complete.')
        return 0
#
#
#
def main():
    """Main program.

    Parameters
    ----------
    None

    Returns
    -------
    main : int
        Exit status that will be passed to ``sys.exit()``.
    """
    di = DesiInstall()
    status = di.run()
    return status
