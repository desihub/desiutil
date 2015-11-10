# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
============
desiutil.svn
============

This package contains code for interacting with DESI svn products.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
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
    proc = Popen(['svnversion', '-n', '.'],
                 universal_newlines=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    # svn 1.7.x says 'Unversioned', svn < 1.7 says 'exported'.
    if out.startswith('Unversioned') or out.startswith('exported'):
        return '0'
    if ':' in out:
        rev = out.split(':')[1]
    else:
        rev = out
    rev = rev.replace('M', '').replace('S', '').replace('P', '')
    return rev


def last_tag(tags, username=None):
    """Scan an SVN tags directory and return the most recent tag.

    Parameters
    ----------
    tags : str
        A URL pointing to an SVN tags directory.
    username : str, optional
        If set, pass the value to SVN's ``--username`` option.

    Returns
    -------
    last_tag : str
        The most recent tag found in ``tags``.
    """
    from distutils.version import StrictVersion as V
    from subprocess import Popen, PIPE
    command = ['svn', '--non-interactive']
    if username is not None:
        command += ['--username', username]
    command += ['ls', tags]
    proc = Popen(command, universal_newlines=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    try:
        mrt = sorted([v.rstrip('/') for v in out.split('\n') if len(v) > 0],
                     key=lambda x: V(x))[-1]
    except IndexError:
        mrt = '0.0.0'
    return mrt


def version(productname, url=None):
    """Returns the version of a package.

    Parameters
    ----------
    productname : str
        The name of the package.

    Returns
    -------
    version : str
        A PEP 386-compatible version string.
    url : str, optional
        If the product is not defined in the known_products file, the url
        can be set this way.

    Notes
    -----
    The version string should be compatible with `PEP 386`_ and
    `PEP 440`_.

    .. _`PEP 386`: http://legacy.python.org/dev/peps/pep-0386/
    .. _`PEP 440`: http://legacy.python.org/dev/peps/pep-0440/
    """
    from .install import known_products
    if productname in known_products:
        myversion = (last_tag(known_products[productname]+'/tags') + '.dev' +
                     last_revision(productname))
    elif url is not None:
        myversion = (last_tag(url+'/tags') + '.dev' +
                     last_revision(productname))
    else:
        myversion = '0.0.1.dev0'
    return myversion
