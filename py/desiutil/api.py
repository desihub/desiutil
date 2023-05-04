# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
============
desiutil.api
============

This package contains code for creating API files for use with Sphinx documentation.
The resulting api file simply has a Sphinx-readable link to every ``*.py`` file.
"""
import os
import sys
from argparse import ArgumentParser
from . import __version__ as desiutilVersion
from .log import log
from .setup import find_version_directory

# Do not generate an API entry for these files.
_exclude_file = ('_version.py', )


def _test_file(d, f):
    """Do not generate an API entry for test files.
    """
    return os.path.basename(d) == 'test' or os.path.basename(d) == 'tests'


def find_modules(name):
    """Find ``*.py`` files in the package directory corresponding to `name`.

    Parameters
    ----------
    name : :class:`str`
        The name of the package.

    Returns
    -------
    :class:`list`
        The modules found in the package.
    """
    productroot = find_version_directory(name)
    modules = []
    for dirpath, dirnames, filenames in os.walk(productroot):
        if dirpath == productroot:
            d = ''
        else:
            d = dirpath.replace(productroot + '/', '')
        log.debug(d)
        for f in filenames:
            mod = [name]
            if f.endswith('.py') and f not in _exclude_file and not _test_file(d, f):
                if d:
                    mod += d.split('/')
                if f != '__init__.py':
                    mod.append(f.replace('.py', ''))
                modules.append('.'.join(mod))
                log.debug('.'.join(mod))
    return modules


def write_api(modules, options):
    """Write out a file containing the modules found.

    Parameters
    ----------
    modules : :class:`list`
        The names of the modules found in the package.
    options: :class:`~argparse.Namespace`
        The command-line options.

    Returns
    -------
    :class:`int`
        An integer suitable for passing to :func:`sys.exit`.
    """
    title = f"{options.name} API"
    lines = ['='*len(title), title, '='*len(title), '']
    for m in sorted(modules):
        lines += [f'.. automodule:: {m}', '    :members:', '']
    if os.path.exists(options.api):
        if options.overwrite:
            log.warning("%s will be overwritten!", options.api)
        else:
            log.error("%s already exists!", options.api)
            return 1
    with open(options.api, 'w') as a:
        a.write('\n'.join(lines))
    return 0


def main():
    """Entry-point for command-line scripts.

    Returns
    -------
    :class:`int`
        An integer suitable for passing to :func:`sys.exit`.
    """
    parser = ArgumentParser(description="Create or update a doc/api.rst file.",
                            prog=os.path.basename(sys.argv[0]))
    parser.add_argument('-a', '--api', dest='api',
                        default=os.path.join(os.path.abspath('.'), 'doc', 'api.rst'),
                        help='Set the name of the API file (default %(default)s).')
    parser.add_argument('-o', '--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite any existing API file.')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + desiutilVersion)
    parser.add_argument('name', help='The top-level name of the package.')
    options = parser.parse_args()

    modules = find_modules(options.name)

    return write_api(modules, options)
