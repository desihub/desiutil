# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
================
desiutil.modules
================

This package contains code for processing and installing `Module files`_.

.. _`Module files`: http://modules.sourceforge.net
"""
import os
import re
import sys
from argparse import ArgumentParser
from shutil import which
from stat import S_IRUSR, S_IRGRP, S_IROTH
from configparser import ConfigParser
from pkg_resources import resource_filename
from . import __version__ as desiutilVersion
from .io import unlock_file
from .log import log


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
    elif os.path.exists(os.path.join(moduleshome, 'libexec', 'lmod')):
        #
        # Lmod version!
        #
        modulecmd = [os.path.join(moduleshome, 'libexec', 'lmod'), 'python']
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
    if working_dir is None:
        working_dir = os.getcwd()
    module_keywords = {'name': product,
                       'version': version,
                       'product_root': product_root,
                       'needs_bin': '# ',
                       'needs_python': '# ',
                       'needs_trunk_py': '# ',
                       'trunk_py_dir': '/py',
                       'needs_ld_lib': '# ',
                       'needs_idl': '# ',
                       'pyversion': "python{0:d}.{1:d}".format(*sys.version_info)}
    if os.path.isdir(os.path.join(working_dir, 'bin')):
        module_keywords['needs_bin'] = ''
    if os.path.isdir(os.path.join(working_dir, 'lib')):
        module_keywords['needs_ld_lib'] = ''
    if os.path.isdir(os.path.join(working_dir, 'pro')):
        module_keywords['needs_idl'] = ''
    if (os.path.exists(os.path.join(working_dir, 'setup.py')) and
        (os.path.isdir(os.path.join(working_dir, product)) or
         os.path.isdir(os.path.join(working_dir, product.lower())))):
        if dev:
            module_keywords['needs_trunk_py'] = ''
            module_keywords['trunk_py_dir'] = ''
        else:
            module_keywords['needs_python'] = ''
    if os.path.isdir(os.path.join(working_dir, 'py')):
        if dev:
            module_keywords['needs_trunk_py'] = ''
        else:
            module_keywords['needs_python'] = ''
    if os.path.isdir(os.path.join(working_dir, 'python')):
        if dev:
            module_keywords['needs_trunk_py'] = ''
            module_keywords['trunk_py_dir'] = '/python'
        else:
            module_keywords['needs_python'] = ''
    if os.path.exists(os.path.join(working_dir, 'setup.cfg')):
        conf = ConfigParser()
        conf.read([os.path.join(working_dir, 'setup.cfg')])
        if conf.has_section('entry_points') or conf.has_section('options.entry_points'):
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

    Note
    ----
    Module files are always installed with world-read permissions.
    """
    if not os.path.isdir(os.path.join(module_dir, module_keywords['name'])):
        os.makedirs(os.path.join(module_dir, module_keywords['name']))
    install_module_file = os.path.join(module_dir, module_keywords['name'],
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

    Note
    ----
    .version files are always installed with world-read permissions.
    """
    dot_template = '#%Module1.0\nset ModulesVersion "{version}"\n'
    install_version_file = os.path.join(module_dir, module_keywords['name'],
                                        '.version')
    dot_version = dot_template.format(**module_keywords)
    _write_module_data(install_version_file, dot_version)
    return dot_version


def _write_module_data(filename, data):
    """Write and permission-lock Module file data.  This is intended
    to consolidate some duplicated code.

    Parameters
    ----------
    filename : :class:`str`
        The module file to write.
    data : :class:`str`
        The data to be written to `filename`.
    """
    with unlock_file(filename, 'w') as f:
        f.write(data)
    p = S_IRUSR | S_IRGRP | S_IROTH
    os.chmod(filename, p)
    return


def main():
    """Entry-point for command-line scripts.

    Returns
    -------
    :class:`int`
        An integer suitable for passing to :func:`sys.exit`.
    """
    parser = ArgumentParser(description="Install a Module file for a DESI software product.",
                            prog=os.path.basename(sys.argv[0]))
    parser.add_argument('-d', '--default', dest='default', action='store_true', help='Mark this Module as default.')
    parser.add_argument('-m', '--modules', dest='modules', help='Set the Module install directory.')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + desiutilVersion)
    parser.add_argument('product', help='Name of product.')
    parser.add_argument('product_version', help='Version of product.')
    options = parser.parse_args()

    if options.modules is None:
        try:
            options.modules = os.path.join('/global/common/software/desi',
                                           os.environ['NERSC_HOST'],
                                           'desiconda',
                                           'current',
                                           'modulefiles')
        except KeyError:
            try:
                options.modules = os.path.join(os.environ['DESI_PRODUCT_ROOT'],
                                               'modulefiles')
            except KeyError:
                log.error("Could not determine a Module install directory!")
                return 1

    dev = ('dev' in options.product_version or
           'main' in options.product_version or
           'master' in options.product_version or
           'branches' in options.product_version or
           'trunk' in options.product_version)
    working_dir = os.path.abspath('.')
    module_keywords = configure_module(options.product, options.product_version, working_dir, dev=dev)
    module_file = os.path.join(working_dir, 'etc', '{0}.module'.format(options.product))

    if not os.path.exists(module_file):
        log.warning("Could not find Module file: %s; using default.", module_file)
        module_file = resource_filename('desiutil', 'data/desiutil.module')

    process_module(module_file, module_keywords, options.modules)

    if options.default:
        default_module(module_keywords, options.modules)

    return 0
