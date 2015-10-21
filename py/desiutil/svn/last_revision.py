# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def last_revision(product):
    """Get the svn revision number.

    Parameters
    ----------
    product : str
        The name of the product.  This will be converted into the
        environment variable that points to the product.

    Returns
    -------
    last_revision : str
        The latest svn revision number.  A revision number of 0 indicates
        an error of some kind.
    """
    from subprocess import Popen, PIPE
    from os import environ
    try:
        path = environ[product.upper()]
    except KeyError:
        try:
            path = environ[product.upper()+'_DIR']
        except KeyError:
            return '0'
    proc = Popen(['svnversion','-n',path],stdout=PIPE,stderr=PIPE)
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
