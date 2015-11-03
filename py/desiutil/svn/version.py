# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def version(productname):
    """Returns the version of a package.

    Parameters
    ----------
    productname : str
        The name of the package.

    Returns
    -------
    version : str
        A PEP 386-compatible version string.

    Notes
    -----
    The version string should be compatible with `PEP 386`_ and
    `PEP 440`_.

    .. _`PEP 386`: http://legacy.python.org/dev/peps/pep-0386/
    .. _`PEP 440`: http://legacy.python.org/dev/peps/pep-0440/
    """
    from ..install import known_products
    from . import last_revision, last_tag
    if productname in known_products:
        myversion = (last_tag(known_products[productname]+'/tags') + '.dev'
            + last_revision(productname))
    else:
        myversion = '0.0.1.dev0'
    return myversion
