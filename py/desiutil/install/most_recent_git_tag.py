# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def most_recent_git_tag(owner,repo,username=None):
    """Scan GitHub tags and return the most recent tag.

    Parameters
    ----------
    owner : str
        The owner or group in GitHub
    repo : str
        Name of the product.

    Returns
    -------
    most_recent_git_tag : str
        The most recent tag found on GitHub.
    """
    from os.path import basename
    import requests
    r = requests.get('https://api.github.com/repos/{0}/{1}/git/refs/tags/'.format(owner,repo))
    data = r.json()
    return basename(data[-1]['ref'])
