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
    from os.path import basename
    from argparse import ArgumentParser
    from desiUtil import version
    #
    # Parse arguments
    #
    executable = basename(argv[0])
    parser = ArgumentParser(description=__doc__,prog=executable)
    parser.add_argument('-d', '--default', action='store_true', dest='default',
        help='Make this version the default version.')
    parser.add_argument('-M', '--module-dir', action='store', dest='moduledir',
        metavar='DIR',help="Install module files in DIR.",default='')
    parser.add_argument('-t', '--test', action='store_true', dest='test',
        help='Test mode.  Do not actually install anything.')
    parser.add_argument('-u', '--url', action='store',dest='url,'
        metavar='URL',help="Download software from URL.",
        default='https://desi.lbl.gov/svn/code')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
        help='Print extra information.')
    parser.add_argument('-V', '--version', action='store_true', dest='version',
        help='Print version information.')
    options = parser.parse_args()
    #
    #
    #
    if options.version:
        vers = version()
        print(vers)
        return 0
    print('Welcome to desiInstall!')
    if options.verbose:
        print('Verbose selected!')
    return 0
#
#
#
if __name__ == '__main__':
    from sys import exit
    exit(main())
