# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
================
desiutil.modules
================

This package contains code for processing and installing `Module files`_.

.. _`Module files`: http://modules.sourceforge.net
"""
from shutil import which


def init_modules(moduleshome=None, method=False, command=False):
    """Set up the Modules infrastructure.

    Parameters
    ----------
    moduleshome : :class:`str`, optional
        The path containing the Modules init code.  If not provided,
        :envvar:`MODULESHOME` will be used.
    method : :class:`bool`, optional
        If ``True`` the function returned will be suitable for converting
        into an instance method.
    command : :class:`bool`, optional
        If ``True``, return the command used to call Modules, rather than
        a function.

    Returns
    -------
    callable
        A function that wraps the ``module()`` function, and deals with
        setting :data:`sys.path`.  Returns ``None`` if no Modules infrastructure
        could be found.
    """
    import os
    import re
    if moduleshome is None:
        try:
            moduleshome = os.environ['MODULESHOME']
        except KeyError:
            return None
    if not os.path.isdir(moduleshome):
        return None
    if 'MODULEPATH' not in os.environ:
        os.environ['MODULEPATH'] = ''
        dot_modulespath = os.path.join(moduleshome, 'init', '.modulespath')
        if os.path.exists(dot_modulespath):
            path = list()
            with open(dot_modulespath, 'r') as f:
                for line in f.readlines():
                    line = re.sub("#.*$", '', line.strip())
                    if line != '':
                        path.append(line)
            os.environ['MODULEPATH'] = ':'.join(path)
        modulerc = os.path.join(moduleshome, 'init', 'modulerc')
        if os.path.exists(modulerc):
            path = list()
            with open(modulerc, 'r') as f:
                for line in f.readlines():
                    line = re.sub("#.*$", '', line.strip())
                    if line != '' and line.startswith('module use'):
                        p = os.path.expanduser(line.replace('module use ', '').strip())
                        path.append(p)
            os.environ['MODULEPATH'] = ':'.join(path)
    if 'LOADEDMODULES' not in os.environ:
        os.environ['LOADEDMODULES'] = ''
    if os.path.exists(os.path.join(moduleshome, 'modulecmd.tcl')):
        #
        # TCL version!
        #
        if 'TCLSH' in os.environ:
            tclsh = os.environ['TCLSH']
        else:
            tclsh = which('tclsh')
        if tclsh is None:
            raise ValueError("TCL Modules detected, but no tclsh excecutable found.")
        modulecmd = [tclsh, os.path.join(moduleshome, 'modulecmd.tcl'), 'python']
    else:
        #
        # This should work on all NERSC systems, assuming the user's environment
        # is not totally screwed up.
        #
        tmpcmd = which('modulecmd')
        if tmpcmd is None:
            raise ValueError("Modules environment detected, but no 'modulecmd' excecutable found.")
        modulecmd = [tmpcmd, 'python']
    if 'MODULE_VERSION' in os.environ:
        os.environ['MODULE_VERSION_STACK'] = os.environ['MODULE_VERSION']
    if command:
        return modulecmd

    def desiutil_module(command, *arguments):
        """Call the Modules command.

        Parameters
        ----------
        command : :class:`str`
            Command passed to the base module command.
        arguments : :class:`list`
            Arguments passed to the module command.

        Returns
        -------
        None

        Notes
        -----
        The base module function does not update :data:`sys.path` to
        reflect any additional directories added to
        :envvar:`PYTHONPATH`.  The wrapper function takes care
        of that (and uses set theory!).

        This module also avoids potential Python 3 conflicts.
        """
        import os
        import subprocess
        from sys import path
        try:
            old_python_path = set(os.environ['PYTHONPATH'].split(':'))
        except KeyError:
            old_python_path = set()
        cmd = modulecmd + [command] + list(arguments)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        status = p.returncode
        # exec out in globals(), locals()
        exec(out, globals(), locals())
        try:
            new_python_path = set(os.environ['PYTHONPATH'].split(':'))
        except KeyError:
            new_python_path = set()
        add_path = new_python_path - old_python_path
        for p in add_path:
            path.insert(int(path[0] == ''), p)
        return
    if method:
        def desiutil_module_method(self, command, *arguments):
            return desiutil_module(command, *arguments)
        desiutil_module_method.__doc__ = desiutil_module.__doc__
        return desiutil_module_method
    return desiutil_module


def configure_module(product, version, product_root, working_dir=None, dev=False):
    """Decide what needs to go in the Module file.

    Parameters
    ----------
    product : :class:`str`
        Name of the product.
    version : :class:`str`
        Version of the product.
    product_root : :class:`str`
        Directory that contains the installed code.
    working_dir : :class:`str`, optional
        The directory to examine.  If not set, the current working directory
        will be used.
    dev : :class:`bool`, optional
        If ``True``, interpret the directory as a 'development' install,
        *e.g.* a trunk or branch install.

    Returns
    -------
    :class:`dict`
        A dictionary containing the module configuration parameters.
    """
    from os import getcwd
    from os.path import exists, isdir, join
    from sys import version_info
    try:
        from ConfigParser import SafeConfigParser
    except ImportError:
        from configparser import ConfigParser as SafeConfigParser
    if working_dir is None:
        working_dir = getcwd()
    module_keywords = {
        'name': product,
        'version': version,
        'product_root': product_root,
        'needs_bin': '# ',
        'needs_python': '# ',
        'needs_trunk_py': '# ',
        'trunk_py_dir': '/py',
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
    if (exists(join(working_dir, 'setup.py')) and isdir(join(working_dir, product))):
        if dev:
            module_keywords['needs_trunk_py'] = ''
            module_keywords['trunk_py_dir'] = ''
        else:
            module_keywords['needs_python'] = ''
    if isdir(join(working_dir, 'py')):
        if dev:
            module_keywords['needs_trunk_py'] = ''
        else:
            module_keywords['needs_python'] = ''
    if isdir(join(working_dir, 'python')):
        if dev:
            module_keywords['needs_trunk_py'] = ''
            module_keywords['trunk_py_dir'] = '/python'
        else:
            module_keywords['needs_python'] = ''
    if exists(join(working_dir, 'setup.cfg')):
        conf = SafeConfigParser()
        conf.read([join(working_dir, 'setup.cfg')])
        if conf.has_section('entry_points'):
            module_keywords['needs_bin'] = ''
    return module_keywords


def process_module(module_file, module_keywords, module_dir):
    """Process a Module file.

    Parameters
    ----------
    module_file : :class:`str`
        A template Module file to process.
    module_keywords : :class:`dict`
        The parameters to use for Module file processing.
    module_dir : :class:`str`
        The directory where the Module file should be installed.

    Returns
    -------
    :class:`str`
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
    _write_module_data(install_module_file, mod)
    return mod


def default_module(module_keywords, module_dir):
    """Install or update a .version file to set the default Module.

    Parameters
    ----------
    module_keywords : :class:`dict`
        The parameters to use for Module file processing.
    module_dir : :class:`str`
        The directory where the Module file should be installed.

    Returns
    -------
    :class:`str`
        The text of the processed .version file.
    """
    from os.path import join
    dot_template = '#%Module1.0\nset ModulesVersion "{version}"\n'
    install_version_file = join(module_dir, module_keywords['name'],
                                '.version')
    dot_version = dot_template.format(**module_keywords)
    _write_module_data(install_version_file, dot_version)
    return dot_version


def _write_module_data(filename, data):
    """Write and permission-lock Module file data.  This is intended
    to consolidate some duplicated code.
    """
    from os import chmod
    from stat import S_IRUSR, S_IRGRP
    from .io import unlock_file
    with unlock_file(filename, 'w') as f:
        f.write(data)
    chmod(filename, S_IRUSR | S_IRGRP)
    return
