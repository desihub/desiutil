# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def version(headurl):
    """Returns the version of a package.

    Parameters
    ----------
    headurl : str
        A svn HeadURL string.

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
    from . import last_revision, last_tag
    if headurl.find('tags') > 0:
        # myproduct = headurl[0:headurl.find('tags')-1].split('/')[-1]
        myversion = headurl[headurl.find('tags')+5:].split('/')[0]
    elif (headurl.find('trunk') > 0) or (headurl.find('branches') > 0):
        url = headurl[10:len(headurl)-2]
        findstr = ('branches','trunk')[int(headurl.find('trunk') > 0)]
        myproduct = headurl[0:headurl.find(findstr)-1].split('/')[-1]
        tagurl = url[0:url.find(findstr)]+'tags'
        myversion = last_tag(tagurl) + '.dev' + last_revision(myproduct)
    else:
        myversion = '0.0.1.dev0'
    return myversion
