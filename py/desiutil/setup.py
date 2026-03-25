# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
==============
desiutil.setup
==============

This module supplies :command:`desi_update_version`, which simplifies
setting and updating version strings in Python packages.

This module also supports *deprecated* ``python setup.py <command>`` actions.

For historical reasons, this module is retains an outdated name ``setup.py``.
"""
import os
import re
import sys
from argparse import ArgumentParser
from . import __version__ as desiutilVersion
from .log import log
from .svn import version as svn_version
from .git import version as git_version


_match_version_line = re.compile(r"""__version__\s*=\s*  # opening part of the line, allow any amount of whitespace including none
                                     (?P<oq>['"])        # match any opening quote and give it the label oq = opening quote
                                     (?P<v>[^'"]+)       # any character not a quote, one or more times, label v = version
                                     (?P=oq)             # match the same opening quote""", re.VERBOSE)


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
    setup_dir = os.path.abspath('.')
    if os.path.isdir(os.path.join(setup_dir, 'py', productname)):
        version_dir = os.path.join(setup_dir, 'py', productname)
    elif os.path.isdir(os.path.join(setup_dir, productname)):
        version_dir = os.path.join(setup_dir, productname)
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
    version_file = os.path.join(version_dir, '_version.py')
    if not os.path.isfile(version_file):
        update_version(productname)
    with open(version_file, "r") as f:
        for line in f.readlines():
            mo = _match_version_line.match(line)
            if mo:
                ver = mo.group('v')
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
        if os.path.isdir(".svn"):
            ver = svn_version(productname)
        elif os.path.isdir(".git"):
            ver = git_version()
        else:
            raise IOError("Could not determine repository type.")
    version_file = os.path.join(version_dir, '_version.py')
    with open(version_file, "w") as f:
        f.write("__version__ = '{}'\n".format(ver))
    return


def main():
    """Entry-point for command-line scripts.

    Returns
    -------
    :class:`int`
        An integer suitable for passing to :func:`sys.exit`.
    """
    parser = ArgumentParser(description="Update a package version string.",
                            prog=os.path.basename(sys.argv[0]))
    parser.add_argument('-t', '--tag', dest='tag', help='Set the version to a name in preparation for tagging.')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + desiutilVersion)
    parser.add_argument('product', help='Name of product.')
    options = parser.parse_args()

    update_version(options.product, tag=options.tag)
    ver = get_version(options.product)
    log.info("Version is now %s.", ver)
    return 0
