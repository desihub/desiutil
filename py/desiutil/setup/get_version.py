# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
import os
import re
from subprocess import Popen, PIPE
from . import update_version
#
def get_version(productname,debug=False):
    """Get the value of ``__version__`` without having to import the module.

    Parameters
    ----------
    productname : str
        The name of the package.
    debug : bool, optional
        Print extra debug information.

    Returns
    -------
    get_version : str
        The value of ``__version__``.
    """
    version_file = os.path.join('py',productname,'_version.py')
    if not os.path.isfile(version_file):
        if debug:
            print('Creating initial version file.')
        update_version(productname,debug=debug)
    ver = 'unknown'
    with open(version_file, "r") as f:
        for line in f.readlines():
            mo = re.match("__version__ = '(.*)'", line)
            if mo:
                ver = mo.group(1)
    return ver
