# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
================
desiutil.modules
================

This package contains code for processing and installing `Module files`_.

.. _`Module files`: http://modules.sourceforge.net
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.


def init_modules(moduleshome=None, method=False):
    """Set up the Modules infrastructure.

    Parameters
    ----------
    moduleshome : str, optional
        The path containing the Modules init code.  If not provided,
        :envvar:`MODULESHOME` will be used.
    method : bool, optional
        If ``True`` the function returned will be suitable for converting
        into an instance method.

    Returns
    -------
    init_modules : function
        A function that wraps the ``module()`` function, and deals with
        setting ``sys.path``.  Returns ``None`` if no Modules infrastructure
        could be found.
    """
    import os
    if moduleshome is None:
        try:
            moduleshome = os.environ['MODULESHOME']
        except KeyError:
            return None
    for modpy in ('python', 'python.py'):
        initpy = os.path.join(moduleshome, 'init', modpy)
        if os.path.exists(initpy):
            execfile(initpy, globals())
            if method:
                def module_method(self, command, *arguments):
                    """Wrap the module function provided by the Modules
                    init script.

                    Parameters
                    ----------
                    command : str
                        Command passed to the base module command.
                    arguments : list
                        Arguments passed to the module command.

                    Returns
                    -------
                    module_wrapper : None
                        Just like the module command.

                    Notes
                    -----
                    The base module function does not update sys.path to
                    reflect any additional directories added to
                    :envvar:`PYTHONPATH`.  The wrapper function takes care
                    of that (and uses set theory!).
                    """
                    from os import environ
                    from sys import path
                    try:
                        old_python_path = set(environ['PYTHONPATH'].split(':'))
                    except KeyError:
                        old_python_path = set()
                    module(command, *arguments)
                    try:
                        new_python_path = set(environ['PYTHONPATH'].split(':'))
                    except KeyError:
                        new_python_path = set()
                    add_path = new_python_path - old_python_path
                    for p in add_path:
                        path.insert(int(path[0] == ''), p)
                    return
                return module_method
            else:
                def module_wrapper(command, *arguments):
                    """Wrap the module function provided by the Modules
                    init script.

                    Parameters
                    ----------
                    command : str
                        Command passed to the base module command.
                    arguments : list
                        Arguments passed to the module command.

                    Returns
                    -------
                    module_wrapper : None
                        Just like the module command.

                    Notes
                    -----
                    The base module function does not update sys.path to
                    reflect any additional directories added to
                    :envvar:`PYTHONPATH`.  The wrapper function takes care
                    of that (and uses set theory!).
                    """
                    from os import environ
                    from sys import path
                    try:
                        old_python_path = set(environ['PYTHONPATH'].split(':'))
                    except KeyError:
                        old_python_path = set()
                    module(command, *arguments)
                    try:
                        new_python_path = set(environ['PYTHONPATH'].split(':'))
                    except KeyError:
                        new_python_path = set()
                    add_path = new_python_path - old_python_path
                    for p in add_path:
                        path.insert(int(path[0] == ''), p)
                    return
                return module_wrapper
    return None


def configure_module(product, version, working_dir=None, dev=False):
    """Decide what needs to go in the Module file.

    Parameters
    ----------
    product : str
        Name of the product.
    version : str
        Version of the product.
    working_dir : str, optional
        The directory to examine.  If not set, the current working directory
        will be used.
    dev : bool, optional
        If ``True``, interpret the directory as a 'development' install,
        *e.g.* a trunk or branch install.

    Returns
    -------
    configure_module : dict
        A dictionary containing the module configuration parameters.
    """
    from os import getcwd
    from os.path import isdir, join
    from sys import version_info
    if working_dir is None:
        working_dir = getcwd()
    module_keywords = {
        'name': product,
        'version': version,
        'needs_bin': '# ',
        'needs_python': '# ',
        'needs_trunk_py': '# ',
        'needs_ld_lib': '# ',
        'needs_idl': '# ',
        'pyversion': "python{0:d}.{1:d}".format(*version_info)
        }
    if isdir(join(working_dir, 'bin')):
        module_keywords['needs_bin'] = ''
    if isdir(join(working_dir, 'lib')):
        module_keywords['needs_ld_lib'] = ''
    if isdir(join(working_dir, 'pro')):
        module_keywords['needs_idl'] = ''
    if isdir(join(working_dir, 'py')):
        if dev:
            module_keywords['needs_trunk_py'] = ''
        else:
            module_keywords['needs_python'] = ''
    return module_keywords


def process_module(module_file, module_keywords, module_dir):
    """Process a Module file.

    Parameters
    ----------
    module_file : str
        A template Module file to process.
    module_keywords : dict
        The parameters to use for Module file processing.
    module_dir : str
        The directory where the Module file should be installed.

    Returns
    -------
    process_module : str
        The text of the processed Module file.
    """
    from os import makedirs
    from os.path import isdir, join
    if not isdir(join(module_dir, module_keywords['name'])):
        makedirs(join(module_dir, module_keywords['name']))
    install_module_file = join(module_dir, module_keywords['name'],
                               module_keywords['version'])
    with open(module_file) as m:
        mod = m.read().format(**module_keywords)
    with open(install_module_file, 'w') as m:
        m.write(mod)
    return mod


def default_module(module_keywords, module_dir):
    """Install or update a .version file to set the default Module.

    Parameters
    ----------
    module_keywords : dict
        The parameters to use for Module file processing.
    module_dir : str
        The directory where the Module file should be installed.

    Returns
    -------
    default_module : str
        The text of the processed .version file.
    """
    from os.path import join
    dot_template = '#%Module1.0\nset ModulesVersion "{version}"\n'
    install_version_file = join(module_dir, module_keywords['name'],
                                '.version')
    with open(install_version_file, 'w') as v:
        v.write(dot_template.format(**module_keywords))
    return dot_version
