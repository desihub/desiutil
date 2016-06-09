#!/usr/bin/env python

"""
Utilities for working with code dependencies stored in FITS headers.

The code name and the code version are stored in pairs of keywords, similar
to how table columns are defined.  e.g.

DEPNAM00 = 'numpy'
DEPVER00 = '1.11'
DEPNAM01 = 'desiutil'
DEPVER01 = '1.4.1'

The functions and Dependencies class provided here provide convenience
wrappers to loop over they keywords looking for a particular dependency
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
    set dependency version for code name

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
                continue

        header[namekey] = name
        header[verkey] = version
        return

    #- if we got this far, we ran out of numbers
    raise IndexError

def getdep(header, name):
    '''
    get dependency version for code name

    Args:
        header : dict-like object to store dependencies
        name : code name string

    Returns version string for name

    raises KeyError if name not tracked in header
    '''
    for i in range(100):
        namekey = 'DEPNAM{:02d}'.format(i)
        verkey = 'DEPVER{:02d}'.format(i)
        if namekey in header:
            if header[namekey] == name:
                return header[verkey]
            else:
                continue
        elif i == 0:
            continue    #- ok if DEPNAM00 is missing; continue to DEPNAME01
        else:
            raise KeyError('{} version not found'.format(name))

def hasdep(header, name):
    '''
    returns True if version for name is tracked in header, otherwise False
    '''
    try:
        version = getdep(header, name)
        return True
    except KeyError:
        return False

class Dependencies(object):
    def __init__(self, header=None):
        '''Initialize Dependencies with dict-like header object
        
        if header is None, use a empty OrderedDict
        '''
        if header is None:
            from collections import OrderedDict
            self.header = OrderedDict()
        else:
            self.header = header

    def __setitem__(self, name, version):
        '''sets version of name'''
        setdep(self.header, name, version)

    def __getitem__(self, name):
        '''returns version of name'''
        return getdep(self.header, name)

    def __iter__(self):
        '''returns iterator over name'''
        for i in range(100):
            namekey = 'DEPNAM{:02d}'.format(i)
            verkey = 'DEPVER{:02d}'.format(i)
            if namekey not in self.header and i==0: continue
            if namekey in self.header:
                yield self.header[namekey]
            else:
                raise StopIteration

        raise StopIteration

    def items(self):
        '''returns iterator over (name, version)'''
        for name in self:
            yield name, self[name]
