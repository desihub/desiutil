# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def set_build_type(working_dir,force=False):
    """Determine the build type.

    Parameters
    ----------
    working_dir : str
        Name of the working directory.
    force : bool, optional
        Set to ``True`` to force the 'make' build type.

    Returns
    -------
    set_build_type : set
        A set containing the detected build types.
    """
    from os.path import exists, isdir, join
    build_type = set(['plain'])
    if force:
        build_type.add('make')
    else:
        if exists(join(working_dir,'setup.py')):
            build_type.add('py')
        if exists(join(working_dir,'Makefile')):
            build_type.add('make')
        else:
            if isdir(join(working_dir,'src')):
                build_type.add('src')
    return build_type
