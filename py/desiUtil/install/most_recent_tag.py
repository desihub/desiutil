# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def most_recent_tag(tags,username=None):
    """Scan an SVN tags directory and return the most recent tag.

    Parameters
    ----------
    tags : str
        A URL pointing to an SVN tags directory.
    username : str, optional
        If set, pass the value to SVN's ``--username`` option.

    Returns
    -------
    most_recent_tag : str
        The most recent tag found in ``tags``.
    """
    import subprocess
    command = ['svn']
    if username is not None:
        command += ['--username', username]
    command += ['ls',tags]
    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = proc.communicate()
    try:
        mrt = sorted([v.rstrip('/') for v in out.split('\n') if len(v) > 0])[-1]
    except IndexError:
        mrt = '0.0.0'
    return mrt
