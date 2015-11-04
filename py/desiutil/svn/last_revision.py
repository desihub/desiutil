# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def last_revision(product):
    """Get the svn revision number.

    Returns
    -------
    last_revision : str
        The latest svn revision number.  A revision number of 0 indicates
        an error of some kind.

    Notes
    -----
    This assumes that you're running ``python setup.py version`` in an
    svn checkout directory.
    """
    from subprocess import Popen, PIPE
    proc = Popen(['svnversion','-n','.'],
        universal_newlines=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    # svn 1.7.x says 'Unversioned', svn < 1.7 says 'exported'.
    if out.startswith('Unversioned') or out.startswith('exported'):
        return '0'
    if ':' in out:
        rev = out.split(':')[1]
    else:
        rev = out
    rev = rev.replace('M','').replace('S','').replace('P','')
    return rev
