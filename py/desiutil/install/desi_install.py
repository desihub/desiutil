# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Install DESI software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
import logging
from os import environ
from os.path import basename, isdir
from sys import argv
from .most_recent_git_tag import most_recent_git_tag
from .. import __version__ as desiUtilVersion
#
#
#
class DesiInstall(object):
    """Code and data that drive the desiInstall script.

    Parameters
    ----------
    debug : bool, optional
        If ``True`` the log level will be set to logging.DEBUG.

    Attributes
    ----------
    executable : str
        The command used to invoke the script.
    ll : int
        The log level.
    options : argparse.Namespace
        The parsed command-line options.

    """
    def __init__(self,debug=False,test=False):
        """Bare-bones initialization.  The only thing done here is setting up
        the logging infrastructure.
        """
        self.executable = basename(argv[0])
        self.ll = logging.INFO
        if debug:
            self.ll = logging.DEBUG
        if test:
            logging.getLogger('desiInstall').addHandler(logging.NullHandler())
        else:
            logging.basicConfig(level=self.ll, format=self.executable+' [%(name)s] Log - %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
        log = logging.getLogger('desiInstall.__init__')
        log.debug('Logging configured, level set to {0}.'.format(logging.getLevelName(self.ll)))
        return
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
        log = logging.getLogger('desiInstall.get_options')
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
            log.debug('Calling parse_args() with: {0}'.format(' '.join(test_args)))
            self.options = parser.parse_args(test_args)
        return self.options
    def sanity_check(self):
        """Sanity check the options.
        """
        log = logging.getLogger('desiInstall.sanity_check')
        if self.options.product == 'NO PACKAGE' or self.options.product_version == 'NO VERSION':
            if self.options.bootstrap:
                self.options.default = True
                self.options.product = 'desihub/desiutil'
                self.options.product_version = most_recent_git_tag('desihub','desiutil')
                log.info("Selected desiutil/{0} for installation.".format(self.options.product_version))
            else:
                log.error("You must specify a product and a version!")
                return 1
        if self.options.moduleshome is None or not isdir(self.options.moduleshome):
            log.error("You do not appear to have Modules set up.")
            return 1
        self.github = False
        if 'github' in self.options.url:
            self.github = True
            log.debug("Detected GitHub install.")
        return 0
    def run(self):
        """This method wraps all the standard steps of the desiInstall script.

        Parameters
        ----------
        None

        Returns
        -------
        run : int
            An integer suitable for passing to sys.exit.
        """
        log = logging.getLogger('desiInstall.run')
        log.debug('Commencing run().')
        self.get_options()
        status = self.sanity_check()
        log.debug('run() complete.')
        return status
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
    di = DesiInstall(debug=True)
    status = di.run()
    return status
