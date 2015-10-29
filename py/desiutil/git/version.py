# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def version(git='git'):
    """Use ``git describe`` to generate a version string.

    Parameters
    ----------
    git : str, optional
        Path to the git executable, if not in :envvar:`PATH`.

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
    import re
    dirty = re.compile('([0-9.]+)-([0-9]+)-(g[0-9a-f]+)(-dirty|)')
    from subprocess import Popen, PIPE
    myversion = '0.0.1.dev0'
    try:
        p = Popen([git, "describe", "--tags", "--dirty", "--always"], stdout=PIPE)
    except OSError:
        return myversion
    out = p.communicate()[0]
    if p.returncode != 0:
        return myversion
    m = dirty.match(out)
    if m is None:
        return out.rstrip()
    else:
        return '.dev'.join(m.groups()[0:2])
