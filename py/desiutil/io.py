# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
===========
desiutil.io
===========

Module for I/O related code.
"""
import os
import stat
import warnings
from contextlib import contextmanager
import numpy as np
from astropy.table import Table


def combine_dicts(dict1, dict2):
    """Combine two :class:`dict` objects into one, respecting common keys.

    If `dict1` and `dict2` both have key ``a``, then ``dict1[a]`` and
    ``dict2[a]`` must both be dictionaries to recursively merge.

    Parameters
    ----------
    dict1 : :class:`dict`
        First dictionary.
    dict2 : :class:`dict`
        Second dictionary.

    Returns
    -------
    :class:`dict`
        The combined dictionary.

    Raises
    ------
    ValueError
        If the values for a common key are not both :class:`dict`.
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
    if isinstance(obj, (np.float64, np.float32)):
        obj = float(obj)
    elif isinstance(obj, (np.int32, np.int64, np.int16)):
        obj = int(obj)
    elif isinstance(obj, np.bool_):
        obj = bool(obj)
    elif isinstance(obj, (np.string_, str)):
        obj = str(obj)
    # elif isinstance(obj, Quantity):
    #     obj = dict(value=obj.value, unit=obj.unit.to_string())
    elif isinstance(obj, np.ndarray):  # Must come after Quantity
        obj = obj.tolist()
    elif isinstance(obj, dict):
        # First convert keys
        nobj = {}
        for key, value in obj.items():
            nobj[str(key)] = value
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
    '''Parse `dtype` to find its size.

    For example, ``<U14`` returns 14.

    Parameters
    ----------
    dtype : :class:`numpy.dtype`
        Dtype object.

    Returns
    -------
    :class:`int`
        The size of the type.

    Notes
    -----
    This is different from ``dtype.itemsize``, which is number of bytes.
    '''
    i = dtype.str.find(dtype.kind)
    return int(dtype.str[i+1:])


def _pick_encoding(table, encoding):
    '''Pick which encoding to use; giving warning if options are in conflict.

    Parameters
    ----------
    table : :class:`astropy.table.Table`
        Table object.
    encoding : :class:`str`
        Encoding to use.  If ``None``, use ``table.meta['ENCODING']``.

    Returns
    -------
    :class:`str`
        The chosen encoding.

    Raises
    ------
    UnicodeError
        If no enoding could be found at all.

    Notes
    -----
    `encoding` trumps ```table.meta['ENCODING']``.
    '''
    if encoding is None:
        if 'ENCODING' in table.meta:
            encoding = table.meta['ENCODING']
        else:
            raise UnicodeError('No encoding given as argument or in table metadata')
    elif 'ENCODING' in table.meta and table.meta['ENCODING'] != encoding:
        message = """data.metadata['ENCODING']=='{}' does not match option '{}';
use encoding=None to use data.metadata['ENCODING'] instead""".format(table.meta['ENCODING'], encoding)
        warnings.warn(message)

    return encoding


def encode_table(data, encoding='ascii'):
    '''Encode unicode strings in a table into bytes using ``numpy.char.encode``.

    Parameters
    ----------
    data : numpy structured array or :class:`~astropy.table.Table`
        Data for conversion.
    encoding : :class:`str`, optional
        Encoding to use for converting unicode to bytes;
        default 'ascii' (FITS and HDF5 friendly);
        if ``None``, try ``ENCODING`` keyword in `data` instead.

    Returns
    -------
    :class:`~astropy.table.Table`
        Table with unicode columns converted to bytes.

    Raises
    ------
    UnicodeEncodeError
        If any input strings cannot be encoded using the specified encoding.
    UnicodeError
        If no encoding is given as argument or in table metadata.

    Notes
    -----
    `encoding` option overides ``data.meta['ENCODING']``;
    use ``encoding=None`` to use ``data.meta['ENCODING']`` instead.
    '''

    try:
        table = Table(data, copy=False)
    except ValueError:  # https://github.com/astropy/astropy/issues/5298
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
    '''Decode byte strings in a table into unicode strings.

    Parameters
    ----------
    data : numpy structured array or :class:`~astropy.table.Table`
        Data for conversion.
    encoding : :class:`str`, optional
        Encoding to use for converting bytes into unicode;
        default 'ascii'; if ``None``, try ``ENCODING`` keyword in `data` instead.
    native : :class:`bool`, optional
        If `True` (default), only decode if native str type is unicode
        (*i.e.* python3 but not python2)

    Returns
    -------
    :class:`~astropy.table.Table`
        Decoded data.

    Notes
    -----
    `encoding` option overides ``data.meta['ENCODING']``;
    use ``encoding=None`` to use ``data.meta['ENCODING']`` instead.
    '''
    try:
        table = Table(data, copy=False)
    except ValueError:  # https://github.com/astropy/astropy/issues/5298
        table = Table(data, copy=True)

    # Check if native str type is bytes
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


@contextmanager
def unlock_file(*args, **kwargs):
    """Unlock a read-only file, return a file-like object, and restore the
    read-only state when done.  Arguments are the same as :func:`open`.

    Returns
    -------
    file-like
        A file-like object, as returned by :func:`open`.

    Notes
    -----
    * This assumes that the user of this function is also the owner of the
      file. :func:`os.chmod` would not be expected to work in any other
      circumstance.
    * Technically, this restores the *original* permissions of the file, it
      does not care what the original permissions were.
    * If the named file does not exist, this function effectively does not
      attempt to guess what the final permissions of the file would be.  In
      other words, it just does whatever :func:`open` would do.  In this case
      it is the user's responsibilty to change permissions as needed after
      creating the file.

    Examples
    --------
    >>> with unlock_file('read-only.txt', 'w') as f:
    ...     f.write(new_data)
    """
    w = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    #
    # Get original permissions, unlock permissions
    #
    # uid = os.getuid()
    old_mode = None
    if os.path.exists(args[0]):
        old_mode = stat.S_IMODE(os.stat(args[0]).st_mode)
        os.chmod(args[0], old_mode | stat.S_IWUSR)
    f = open(*args, **kwargs)
    try:
        yield f
    finally:
        #
        # Restore permissions to read-only state.
        #
        f.close()
        if old_mode is None:
            old_mode = stat.S_IMODE(os.stat(args[0]).st_mode)
        os.chmod(args[0], old_mode & ~w)
