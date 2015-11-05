# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Set up the Modules infrastructure.
"""
def init_modules(moduleshome=None,method=False):
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
    for modpy in ('python','python.py'):
        initpy = os.path.join(moduleshome,'init',modpy)
        if os.path.exists(initpy):
            execfile(initpy,globals())
            if method:
                def module_method(self,command,*arguments):
                    """Wrap the module function provided by the Modules init script.

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
                    module(command,*arguments)
                    try:
                        new_python_path = set(environ['PYTHONPATH'].split(':'))
                    except KeyError:
                        new_python_path = set()
                    add_path = new_python_path - old_python_path
                    for p in add_path:
                        path.insert(int(path[0] == ''),p)
                    return
                return module_method
            else:
                def module_wrapper(command,*arguments):
                    """Wrap the module function provided by the Modules init script.

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
                    module(command,*arguments)
                    try:
                        new_python_path = set(environ['PYTHONPATH'].split(':'))
                    except KeyError:
                        new_python_path = set()
                    add_path = new_python_path - old_python_path
                    for p in add_path:
                        path.insert(int(path[0] == ''),p)
                    return
                return module_wrapper
    return None
