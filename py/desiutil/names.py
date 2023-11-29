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
    Length of target_ra and target_dec must be the same if providing an
    array or list. Note that these names are not unique for roughly
    one percent of DESI targets, so also including TARGETID in
    publications is highly recommended for uniqueness.

    Parameters
    ----------
    target_ra: array of :class:`float64`
        Right ascension in degrees of target object(s). Can be float, double,
         or array/list of floats or doubles
    target_dec: array of :class:`float64`
        Declination in degrees of target object(s). Can be float, double,
         or array/list of floats or doubles

    Returns
    -------
    array of :class:`str`
        The DESI names referring to the input target RA and DEC's. Array is
        the same length as the input arrays.

    """
    # Convert to numpy array in case inputs are scalars or lists
    target_ra, target_dec = np.atleast_1d(target_ra), np.atleast_1d(target_dec)

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
        desiname = 'DESI J' + ra[:-precision].zfill(3) + '.' + ra[-precision:]
        # Positive numbers need an explicit "+" while negative numbers
        #   already have a "-".
        # zfill works properly with '-' but counts it in number of characters
        #   so need one more
        if dec.startswith('-'):
            desiname += dec[:-precision].zfill(3) + '.' + dec[-precision:]
        else:
            desiname += '+' + dec[:-precision].zfill(2) + '.' + dec[-precision:]
        desinames.append(desiname)

    return np.array(desinames)
