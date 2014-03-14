# License information goes here
# -*- coding: utf-8 -*-
"""Install DESI software.
"""
from __future__ import print_function
# The line above will help with 2to3 support.
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
    from sys import argv
    from os import environ, getenv
    from os.path import basename, isdir, join
    from argparse import ArgumentParser
    from desiUtil import version
    import subprocess
    #
    # Parse arguments
    #
    executable = basename(argv[0])
    parser = ArgumentParser(description=__doc__,prog=executable)
    parser.add_argument('-d', '--default', action='store_true', dest='default',
        help='Make this version the default version.')
    parser.add_argument('-F', '--force', action='store_true', dest='force',
        help='Overwrite any existing installation of this product/version.')
    parser.add_argument('-m', '--module-home', action='store', dest='moduleshome',
        metavar='DIR',help='Set or override the value of $MODULESHOME',
        default=getenv('MODULESHOME'))
    parser.add_argument('-M', '--module-dir', action='store', dest='moduledir',
        metavar='DIR',help="Install module files in DIR.",default='')
    parser.add_argument('-t', '--test', action='store_true', dest='test',
        help='Test mode.  Do not actually install anything.')
    parser.add_argument('-u', '--url', action='store',dest='url',
        metavar='URL',help="Download software from URL.",
        default='https://desi.lbl.gov/svn/code')
    parser.add_argument('-U', '--username', action='store', dest='username',
        metavar='USER',help="Set svn username to USER.",default=getenv('USER'))
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
        help='Print extra information.')
    parser.add_argument('-V', '--version', action='store_true', dest='version',
        help='Print version information.')
    parser.add_argument('product',help='Name of product to install.')
    parser.add_argument('product_version',help='Version of product to install.')
    options = parser.parse_args()
    #
    # Print version if requested.
    #
    if options.version:
        vers = version()
        print(vers)
        return 0
    #
    # Set up Modules
    #
    if options.moduleshome is None or not isdir(options.moduleshome):
        print("You do not appear to have Modules set up.")
        return 1
    initpy = join(options.moduleshome,'init','python.py')
    execfile(initpy,globals())
    #
    # Determine the product and version names.
    #
    baseproduct = basename(options.product)
    baseversion = basename(options.product_version)
    is_branch = options.product_version.startswith('branches')
    is_trunk = options.product_version == 'trunk'
    if is_trunk or is_branch:
        product_url = join(options.url,options.product,options.product_version)
    else:
        product_url = join(options.url,options.product,'tags',options.product_version)
    #
    # Check for existence of the URL.
    #
    command = ['svn','--username',options.username,'ls',product_url]
    if options.verbose:
        print(' '.join(command))
    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if options.verbose:
        print(out)
        print(err)
    return 0
#
#
#
if __name__ == '__main__':
    from sys import exit
    exit(main())
