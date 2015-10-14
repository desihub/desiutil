# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
import os
from subprocess import Popen, PIPE
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
    if tag is not None:
        ver = tag
    else:
        if not os.path.isdir(".git"):
            print("This is not a git repository.")
            return
        no_git = "Unable to run git, leaving py/{0}/_version.py alone.".format(productname)
        try:
            p = Popen(["git", "describe", "--tags", "--dirty", "--always"], stdout=PIPE, stderr=PIPE)
        except EnvironmentError:
            print("Could not run 'git describe'!")
            print(no_git)
            return
        out, err = p.communicate()
        if p.returncode != 0:
            print("Returncode = {0}".format(p.returncode))
            print(no_git)
            return
        ver = out.rstrip().split('-')[0]+'.dev'
        try:
            p = Popen(["git", "rev-list", "--count", "HEAD"], stdout=PIPE, stderr=PIPE)
        except EnvironmentError:
            print("Could not run 'git rev-list'!")
            print(no_git)
            return
        out, err = p.communicate()
        if p.returncode != 0:
            print("Returncode = {0}".format(p.returncode))
            print(no_git)
            return
        ver += out.rstrip()
    version_file = os.path.join('py',productname,'_version.py')
    with open(version_file, "w") as f:
        f.write( "__version__ = '{}'\n".format( ver ) )
    if debug:
        print("Set {0} to {1}".format( version_file, ver ))
    return
