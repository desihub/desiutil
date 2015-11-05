# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
import os
from subprocess import Popen, PIPE
from .find_version_directory import find_version_directory
from ..svn import version as svn_version
from ..git import version as git_version
#
def update_version(productname,tag=None,debug=False):
    """Update the _version.py file.

    Parameters
    ----------
    productname : str
        The name of the package.
    tag : str, optional
        Set the version to this string, unconditionally.
    debug : bool, optional
        Print extra debug information.

    Returns
    -------
    None
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
            print("Could not determine repository type.")
            return
    version_file = os.path.join(version_dir,'_version.py')
    with open(version_file, "w") as f:
        f.write( "__version__ = '{}'\n".format( ver ) )
    if debug:
        print("Set {0} to {1}".format( version_file, ver ))
    return
