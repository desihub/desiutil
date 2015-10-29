# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def dependencies(modulefile):
    """Process the dependencies for a software product.

    Parameters
    ----------
    modulefile : str
        Name of the module file containing dependencies.

    Returns
    -------
    dependencies : list
        Returns the list of dependencies.  If the module file
        is not found or there are no dependencies, the list will be empty.

    Raises
    ------
    ValueError
        If `modulefile` can't be found.
    """
    from os import environ
    from os.path import exists
    nersc = 'NERSC_HOST' in environ
    if exists(modulefile):
        with open(modulefile) as m:
            lines = m.readlines()
        raw_deps = [l.strip().split()[2] for l in lines if l.strip().startswith('module load')]
    else:
        raise ValueError("Modulefile {0} does not exist!".format(modulefile))
    if nersc:
        hpcp_deps = [d for d in raw_deps if '-hpcp' in d]
        for d in hpcp_deps:
            nd = d.replace("-hpcp","")
            try:
                raw_deps.remove(nd)
            except ValueError:
                pass
        return raw_deps
    else:
        deps = [d for d in raw_deps if '-hpcp' not in d]
        return deps
