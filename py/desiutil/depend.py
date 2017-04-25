# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
===============
desiutil.depend
===============

Utilities for working with code dependencies stored in FITS headers.

The code name and the code version are stored in pairs of keywords, similar
to how table columns are defined. *e.g.*::

    DEPNAM00 = 'numpy'
    DEPVER00 = '1.11'
    DEPNAM01 = 'desiutil'
    DEPVER01 = '1.4.1'

The functions and Dependencies class provide convenience wrappers
to loop over they keywords looking for a particular dependency
and adding a new dependency version to next available DEPNAMnn/DEPVERnn.

Examples:

>>> import desiutil
>>> from desiutil import depend
>>> import astropy
>>> from astropy.io import fits
>>>
>>> hdr = fits.Header()
>>> depend.setdep(hdr, 'desiutil', desiutil.__version__)
>>> depend.setdep(hdr, 'astropy', astropy.__version__)
>>> depend.getdep(hdr, 'desiutil')
'1.4.1.dev316'
>>> depend.hasdep(hdr, 'astropy')
True
>>> hdr
DEPNAM00= 'desiutil'
DEPVER00= '1.4.1.dev316'
DEPNAM01= 'astropy '
DEPVER01= '1.1.1   '

There is also an object wrapper that gives a header dict-like semantics to
update or view dependencies.  This directly updates the input header object
so that it can be used in subsequent I/O

>>> codever = depend.Dependencies(hdr)
>>> codever['blat'] = '1.2'
>>> codever['foo'] = '3.4'
>>> for codename, version in codever.items():
...     print(codename, version)
...
('desiutil', '1.4.1.dev316')
('astropy', u'1.1.1')
('blat', '1.2')
('foo', '3.4')

"""


def setdep(header, name, version):
    '''
    Set dependency version for code name.

    Args:
        header : dict-like object to store dependencies
        name : code name string
        version : version string
    '''
    for i in range(100):
        namekey = 'DEPNAM{:02d}'.format(i)
        verkey = 'DEPVER{:02d}'.format(i)
        if namekey in header:
            if header[namekey] == name:
                header[verkey] = version
                return
        else:
            header[namekey] = name
            header[verkey] = version
            return

    # if we got this far, we ran out of numbers
    raise IndexError("Too many versions to track!")


def getdep(header, name):
    '''
    Get dependency version for code name.

    Args:
        header : dict-like object to store dependencies
        name : code name string

    Returns version string for name

    Raises KeyError if name not tracked in header
    '''
    for i in range(100):
        namekey = 'DEPNAM{:02d}'.format(i)
        verkey = 'DEPVER{:02d}'.format(i)
        if namekey in header:
            if header[namekey] == name:
                return header[verkey]
        elif i == 0:
            continue  # ok if DEPNAM00 is missing; continue to DEPNAME01
        else:
            raise KeyError('{} version not found'.format(name))


def hasdep(header, name):
    '''
    Returns ``True`` if version for name is tracked in header, otherwise ``False``.
    '''
    try:
        version = getdep(header, name)
        return True
    except KeyError:
        return False


def iterdep(header):
    '''Returns iterator over (codename, version) tuples'''
    for i in range(100):
        namekey = 'DEPNAM{:02d}'.format(i)
        verkey = 'DEPVER{:02d}'.format(i)
        if namekey not in header and i == 0:
            continue
        if namekey in header:
            yield (header[namekey], header[verkey])
        else:
            raise StopIteration

    raise StopIteration


# default possible dependencies to check in add_dependencies()
possible_dependencies = [
    'numpy', 'scipy', 'astropy', 'yaml', 'matplotlib',
    'requests', 'fitsio', 'h5py', 'mpi4py', 'psycopg2',
    'desiutil', 'desispec', 'desitarget', 'desimodel', 'desisim',
    'redmonster', 'specter', 'speclite', 'specsim',
    ]


def add_dependencies(header, module_names=None, long_python=False):
    '''Adds DEPNAMnn, DEPVERnn keywords to header for imported modules

    Args:
        header : dict-like object, *e.g.* :class:`astropy.io.fits.Header`.

    Options:
        module_names : list of module names to check
            if None, checks desiutil.depend.possible_dependencies
        long_python : If ``True`` use the full, verbose ``sys.version``
            string for the Python version.  Otherwise, use a short
            version, *e.g.*, ``3.5.2``.

    Only adds the dependency keywords if the module has already been
    previously loaded in this python session.  Uses module.__version__
    if available, otherwise "unknown (/path/to/module/)".
    '''
    import sys
    import importlib

    py_version = ".".join(map(str, sys.version_info[0:3]))
    if long_python:
        py_version = sys.version.replace('\n', ' ')
    setdep(header, 'python', py_version)

    if module_names is None:
        module_names = possible_dependencies

    # Set version strings only for modules that have already been loaded
    for module in module_names:
        if module in sys.modules:
            # already loaded, but we need a reference to the module object
            x = importlib.import_module(module)
            if hasattr(x, '__version__'):
                version = x.__version__
            elif hasattr(x, '__path__'):
                # e.g. redmonster doesn't set __version__
                version = 'unknown ({})'.format(x.__path__[0])
            elif hasattr(x, '__file__'):
                version = 'unknown ({})'.format(x.__file__)
            else:
                version = 'unknown'

            setdep(header, module, version)


class Dependencies(object):
    """Dictionary-like object to track dependencies.

    Parameters
    ----------
    header : dict-like, optional
        A dict-like object.  If not provided, a :class:`~collections.OrderedDict`
        will be used.
    """

    def __init__(self, header=None):
        '''Initialize Dependencies with dict-like header object.

        If header is None, use a empty :class:`~collections.OrderedDict`.
        '''
        if header is None:
            from collections import OrderedDict
            self.header = OrderedDict()
        else:
            self.header = header

    def __setitem__(self, name, version):
        '''Sets version of `name`.'''
        setdep(self.header, name, version)

    def __getitem__(self, name):
        '''Returns version of `name`.'''
        return getdep(self.header, name)

    def __iter__(self):
        '''Returns iterator over name.'''
        for name, version in iterdep(self.header):
            yield name

    def items(self):
        '''Returns iterator over (name, version).'''
        return iterdep(self.header)
