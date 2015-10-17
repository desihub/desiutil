# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Get options for desiInstall.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def desiInstall_options(test_args=None):
    """Parse command-line arguments passed to the desiInstall script.

    Parameters
    ----------
    test_args : list
        Normally, this function is called without arguments, and ``sys.argv``
        is parsed.  Arguments should only be passed for testing purposes.

    Returns
    -------
    desiInstall_options : argparse.Namespace
        A simple object containing the parsed options.
    """
    from sys import argv
    from os import getenv
    from os.path import basename
    from argparse import ArgumentParser
    from .. import __version__ as desiUtilVersion
    xct = basename(argv[0])
    parser = ArgumentParser(description="Install DESI software.",prog=xct)
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
        default=getenv('MODULESHOME'))
    parser.add_argument('-M', '--module-dir', action='store', dest='moduledir',
        metavar='DIR',help="Install module files in DIR.",default='')
    parser.add_argument('-p', '--python', action='store', dest='python',
        metavar='PYTHON',help="Use the Python executable PYTHON (e.g. /opt/local/bin/python2.7).  This option is only relevant when installing desiutil itself.")
    parser.add_argument('-r', '--root', action='store', dest='root',
        metavar='DIR', help='Set or override the value of $DESI_PRODUCT_ROOT',
        default=getenv('DESI_PRODUCT_ROOT'))
    parser.add_argument('-t', '--test', action='store_true', dest='test',
        help='Test mode.  Do not actually install anything.')
    parser.add_argument('-u', '--url', action='store',dest='url',
        metavar='URL',help="Download software from URL.",
        default='https://desi.lbl.gov/svn/code')
    parser.add_argument('-U', '--username', action='store', dest='username',
        metavar='USER',help="Set svn username to USER.",default=getenv('USER'))
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
        options = parser.parse_args()
    else:
        options = parser.parse_args(test_args)
    return options
