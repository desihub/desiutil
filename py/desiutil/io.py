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
import numpy as np

try:
    basestring
except NameError:  # For Python 3
    basestring = str


def yamlify(obj, debug=False):
    """Recursively process an object so it can be serialised for yaml.
    Based on jsonify in linetools.

    Note: All keys in :class:`dict`s are converted to :class:`str`.

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
    elif isinstance(obj, (np.string_, basestring)):
        obj = str(obj)
    # elif isinstance(obj, Quantity):
    #     obj = dict(value=obj.value, unit=obj.unit.to_string())
    elif isinstance(obj, np.ndarray):  # Must come after Quantity
        obj = obj.tolist()
    elif isinstance(obj, dict):
        # First convert keys
        obj = {str(key): value for key, value in obj.items()}
        # Now recursive
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
