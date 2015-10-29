# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def last_tag(owner,repo):
    """Scan GitHub tags and return the most recent tag.

    Parameters
    ----------
    owner : str
        The owner or group in GitHub
    repo : str
        Name of the product.

    Returns
    -------
    last_tag : str
        The most recent tag found on GitHub.
    """
    from os.path import basename
    import requests
    api_url = 'https://api.github.com/repos/{0}/{1}/git/refs/tags/'.format(owner,repo)
    r = requests.get(api_url)
    data = r.json()
    try:
        return basename(data[-1]['ref'])
    except KeyError:
        return '0.0.0'
