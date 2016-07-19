# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
============
desiutils.io
============

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
