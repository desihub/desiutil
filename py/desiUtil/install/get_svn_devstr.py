# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def get_svn_devstr(product):
    """Get the svn revision number.

    Parameters
    ----------
    product : str
        The name of the product.  This will be converted into the
        environment variable that points to the product.

    Returns
    -------
    get_svn_devstr : str
        The latest svn revision number.  A revision number of 0 indicates
        an error of some kind.
    """
    from subprocess import Popen, PIPE
    from os import getenv
    path = getenv(product.upper()+'_DIR')
    if path is None:
        return '0'
    proc = Popen(['svnversion','-n',path],stdout=PIPE,stderr=PIPE)
    out, err = proc.communicate()
    rev = out
    if rev == 'Unversioned directory':
        return '0'
    if ':' in out:
        rev = out.split(':')[1]
    rev = rev.replace('M','').replace('S','').replace('P','')
    return rev
