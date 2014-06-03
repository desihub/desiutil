# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def get_svn_devstr():
    """Get the svn revision number.

    Parameters
    ----------
    None

    Returns
    -------
    get_svn_devstr : str
        The latest svn revision number.

    Bugs
    ----
    This calls svnversion on the current working directory, which
    is not necessarily the same as the svn working directory path.
    """
    from subprocess import Popen, PIPE
    proc = Popen(['svnversion','-n'],stdout=PIPE,stderr=PIPE)
    out, err = proc.communicate()
    rev = out
    if rev == 'Unversioned directory':
        return '666'
    if ':' in out:
        rev = out.split(':')[1]
    rev = rev.replace('M','').replace('S','').replace('P','')
    return rev
