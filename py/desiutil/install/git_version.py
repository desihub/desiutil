# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def git_version(git='git'):
    """Use ``git describe`` to generate a version string.

    Parameters
    ----------
    git : str, optional
        Path to the git executable, if not in :envvar:`PATH`.

    Returns
    -------
    git_version : str
        A version string.
    """
    from subprocess import Popen, PIPE
    myversion = '0.0.1.dev'
    try:
        p = Popen([git, "describe", "--tags", "--dirty", "--always"], stdout=PIPE)
    except EnvironmentError:
        return myversion
    out = p.communicate()[0]
    if p.returncode != 0:
        return myversion
    return out.rstrip()
