# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
===========
desiutil.io
===========

Module for I/O related code.
"""
from __future__ import (print_function, absolute_import, division,
                        unicode_literals)

try:
    basestring
except NameError:  # For Python 3
    basestring = str


def combine_dicts(dict1, dict2):
    """ Combine two dicts into one, respecting common keys
    If dict1 and dict2 both have key a, then x[a] and y[a] must both
    be dictionaries to recursively merge.

    Args:
        dictionary1 : dict
        dictionary2 : dict
    Returns:
        output : dict
    """
    output = {}
    cdict2 = dict2.copy()
    for item, value in dict1.items():
        if item in cdict2:
            if (not isinstance(cdict2[item], dict)) or (not isinstance(dict1[item], dict)):
                    raise ValueError("Overlapping leafs must both be dicts")
            try:
                output[item] = combine_dicts(value, cdict2.pop(item))
            except AttributeError:
                raise AttributeError("Cannot mix dicts with scalar and dict on the same key")
        else:
            output[item] = value
    for item, value in cdict2.items():
         output[item] = value
    # Return
    return output


def yamlify(obj, debug=False):
    """Recursively process an object so it can be serialised for yaml.
    Based on jsonify in `linetools <https://pypi.python.org/pypi/linetools>`_.

    Note: All string-like keys in :class:`dict` s are converted to
    :class:`str`.

    Parameters
    ----------
    obj : :class:`object`
        Any object.
    debug : :class:`bool`, optional
        Print extra information if requested.

    Returns
    -------
    :class:`object`
       An object suitable for yaml serialization.  For example
       :class:`numpy.ndarray` is converted to :class:`list`,
       :class:`numpy.int64` is converted to :class:`int`, etc.
    """
    import numpy as np
    if isinstance(obj, (np.float64, np.float32)):
        obj = float(obj)
    elif isinstance(obj, (np.int32, np.int64, np.int16)):
        obj = int(obj)
    elif isinstance(obj, np.bool_):
        obj = bool(obj)
    elif isinstance(obj, (np.string_, basestring)):
        obj = str(obj)
    # elif isinstance(obj, Quantity):
    #     obj = dict(value=obj.value, unit=obj.unit.to_string())
    elif isinstance(obj, np.ndarray):  # Must come after Quantity
        obj = obj.tolist()
    elif isinstance(obj, dict):
        # First convert keys
        nobj = {}
        for key, value in obj.items():
            if isinstance(key, basestring):
                nobj[str(key)] = value
            else:
                nobj[key] = value
        # Now recursive
        obj = nobj
        for key, value in obj.items():
            obj[key] = yamlify(value, debug=debug)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            obj[i] = yamlify(item, debug=debug)
    elif isinstance(obj, tuple):
        obj = list(obj)
        for i, item in enumerate(obj):
            obj[i] = yamlify(item, debug=debug)
        obj = tuple(obj)
    # elif isinstance(obj, Unit):
    #     obj = obj.name
    # elif obj is u.dimensionless_unscaled:
    #     obj = 'dimensionless_unit'
    if debug:
        print(type(obj))
    return obj

def _dtype_size(dtype):
    '''
    Parse dtype like '<Un' into int(n)
    Note that this is different from dtype.itemsize, which is number of bytes
    '''
    i = dtype.str.find(dtype.kind)
    return int(dtype.str[i+1:])

def _pick_encoding(table, encoding):
    '''
    pick which encoding to use; giving warning if options are in conflict

    Args:
        table : astropy Table object
        encoding : (str) encoding to use; None to use table.meta['ENCODING']

    Note: `encoding` trumps `table.meta['ENCODING']`
    '''
    if encoding is None:
        if 'ENCODING' in table.meta:
            encoding = table.meta['ENCODING']
        else:
            raise UnicodeError('No encoding given as argument or in table metadata')
    elif 'ENCODING' in table.meta and table.meta['ENCODING'] != encoding:
        import warnings
        message = """\
data.metadata['ENCODING']=='{}' does not match option '{}';
use encoding=None to use data.metadata['ENCODING'] instead""".format(\
            table.meta['ENCODING'], encoding)
        warnings.warn(message)

    return encoding

def encode_table(data, encoding='ascii'):
    '''
    Encode unicode strings in a table into bytes using numpy.char.encode

    Args:
        data : numpy structured array or astropy Table

    Options:
        encoding : encoding to use for converting unicode to bytes.
            Default 'ascii' (FITS and HDF5 friendly), but if None,
            use ENCODING from table metadata if available

    Returns astropy Table with unicode columns converted to bytes

    Raises:
        UnicodeEncodeError if any input strings cannot be encoded using
            the specified encoding
        UnicodeError if no encoding is given as argument or in table metadata

    Note: `encoding` option overides data.meta['ENCODING'];
        use encoding=None to use data.meta['ENCODING'] instead
    '''
    from astropy.table import Table
    import numpy as np

    try:
        table = Table(data, copy=False)
    except ValueError:  #- https://github.com/astropy/astropy/issues/5298
        table = Table(data, copy=True)

    encoding = _pick_encoding(table, encoding)

    for col in table.colnames:
        dtype = table[col].dtype
        if dtype.kind == 'U':
            Sn = 'S{}'.format(_dtype_size(dtype))
            table.replace_column(col, np.char.encode(table[col], encoding=encoding).astype(Sn))

    table.meta['ENCODING'] = encoding
    return table

def decode_table(data, encoding='ascii', native=True):
    '''
    Decode byte strings in a table into unicode strings

    Args:
        data : numpy structured array or astropy Table

    Options:
        encoding : encoding to use for converting bytes into unicode;
            default 'ascii'; if None, try ENCODING keyword in data instead
        native : if True (default), only decode if native str type is unicode
            (i.e. python3 but not python2)

    Note: `encoding` option overides data.meta['ENCODING'];
        use encoding=None to use data.meta['ENCODING'] instead
    '''
    from astropy.table import Table
    import numpy as np
    try:
        table = Table(data, copy=False)
    except ValueError:  #- https://github.com/astropy/astropy/issues/5298
        table = Table(data, copy=True)

    #- Check if native str type is bytes
    if native and np.str_('a').dtype.kind == 'S':
        return table

    encoding = _pick_encoding(table, encoding)
    for col in table.colnames:
        dtype = table[col].dtype
        if dtype.kind == 'S':
            Un = 'U{}'.format(_dtype_size(dtype))
            table.replace_column(col, np.char.decode(table[col], encoding=encoding).astype(Un))

    table.meta['ENCODING'] = encoding
    return table
