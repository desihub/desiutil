# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
import os
#
def find_version_directory(productname,debug=False):
    """Return the name of a directory containing version information.

    Looks for files in the following places:

    * py/`productname`/_version.py
    * `productname`/_version.py

    Parameters
    ----------
    productname : str
        The name of the package.
    debug : bool, optional
        Print extra debug information.

    Returns
    -------
    find_version_directory : str
        Name of a directory that can or does contain version information.

    Raises
    ------
    IOError
        If no valid directory can be found.
    """
    setup_dir = os.path.abspath('.')
    if os.path.isdir(os.path.join(setup_dir,'py',productname)):
        version_dir = os.path.join(setup_dir,'py',productname)
    elif os.path.isdir(os.path.join(setup_dir,productname)):
        version_dir = os.path.join(setup_dir,productname)
    else:
        raise IOError("Could not find a directory containing version information!")
    return version_dir
