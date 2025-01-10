# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
==============
desiutil.names
==============

This package contains functions for naming 'things' in DESI
or decoding those names.
"""
import numpy as np


def radec_to_desiname(target_ra, target_dec):
    """Convert the right ascension and declination of a DESI target
    into the corresponding "DESINAME" for reference in publications.
    Length of `target_ra` and `target_dec` must be the same if providing an
    array or list. Note that these names are not unique for roughly
    one percent of DESI targets, so also including TARGETID in
    publications is highly recommended for uniqueness.

    Parameters
    ----------
    target_ra: array of :class:`~numpy.float64`
        Right ascension in degrees of target object(s). Can be float, double,
        or array/list of floats or doubles.
    target_dec: array of :class:`~numpy.float64`
        Declination in degrees of target object(s). Can be float, double,
        or array/list of floats or doubles.

    Returns
    -------
    array of :class:`str`
        The DESI names referring to the input target RA and DEC's. Array is
        the same length as the input arrays.

    Raises
    ------
    ValueError
        If any input values are out of bounds.
    """
    # Convert to numpy array in case inputs are scalars or lists
    target_ra, target_dec = np.atleast_1d(target_ra), np.atleast_1d(target_dec)

    base_tests = [('NaN values', np.isnan),
                  ('Infinite values', np.isinf),]
    inputs = {'target_ra': {'data': target_ra,
                            'tests': base_tests + [('RA not in range [0, 360)', lambda x: (x < 0) | (x >= 360))]},
              'target_dec': {'data': target_dec,
                             'tests': base_tests + [('Dec not in range [-90, 90]', lambda x: (x < -90) | (x > 90))]}}
    for coord in inputs:
        for message, check in inputs[coord]['tests']:
            if check(inputs[coord]['data']).any():
                raise ValueError(f"{message} detected in {coord}!")

    # Number of decimal places in final naming convention
    precision = 4

    # Truncate decimals to the given precision
    ratrunc = np.trunc((10 ** precision) * target_ra).astype(int).astype(str)
    dectrunc = np.trunc((10 ** precision) * target_dec).astype(int).astype(str)

    # Loop over input values and create DESINAME as: DESI JXXX.XXXX+/-YY.YYYY
    # Here J refers to J2000, which isn't strictly correct but is the closest
    #   IAU compliant term
    desinames = []
    for ra, dec in zip(ratrunc, dectrunc):
        zra = ra.zfill(3 + precision)  # RA always has 3 leading digits.
        desiname = 'DESI J' + zra[:-precision] + '.' + zra[-precision:]
        # Positive numbers need an explicit "+" while negative numbers
        #   already have a "-".
        # zfill works properly with '-' but counts it in the number of characters
        #   so need one extra character is needed.
        if dec.startswith('-'):
            zdec = dec.zfill(3 + precision)  # 2 leading digits plus space for '-'.
            desiname += zdec[:-precision] + '.' + zdec[-precision:]
        else:
            zdec = dec.zfill(2 + precision)  # 2 leading digits and the '+' is added explicitly.
            desiname += '+' + zdec[:-precision] + '.' + zdec[-precision:]
        desinames.append(desiname)

    return np.array(desinames)
