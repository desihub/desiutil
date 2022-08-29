# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
==============
desiutil.setup
==============

This package contains code that might be useful in DESI setup.py files.
"""
import os
import re
import sys
from setuptools import Command
from distutils.log import DEBUG, INFO, WARN, ERROR
from .svn import version as svn_version
from .git import version as git_version


class DesiVersion(Command):
    """Allow users to easily update the package version with
    ``python setup.py version``.
    """
    description = "update _version.py from git repo"
    user_options = [('tag=', 't',
                     'Set the version to a name in preparation for tagging.'),
                    ]
    boolean_options = []

    def initialize_options(self):
        self.tag = None

    def finalize_options(self):
        pass

    def run(self):
        meta = self.distribution.metadata
        update_version(meta.get_name(), tag=self.tag)
        ver = get_version(meta.get_name())
        self.announce("Version is now {}.".format(ver), level=INFO)


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
            mo = re.match("__version__ = '(.*)'", line)
            if mo:
                ver = mo.group(1)
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
