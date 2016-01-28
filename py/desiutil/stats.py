# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
==================
desiutils.funcfits
==================

Module for fitting simple functions to 1D arrays

J. Xavier Prochaska, UC Santa Cruz
Fall 2015

.. _desispec: http://desispec.readthedocs.org
"""
from __future__ import print_function, absolute_import, division, unicode_literals

import numpy as np
from scipy.interpolate import interp1d
#import pdb


def perc(x, per=0.68):
    """ Calculate the percentile bounds of a distribution,
    i.e. for per=0.68, the code returns the upper and lower bounds
    that encompass 68percent of the distribution.

    Uses simple interpolation

    Parameters
    ----------
      x : float
        numpy array of values
      per : float, optional
          Percentile for the calculation

    Returns
    -------
      xper : array
        Value at lower, value at upper
    """
    #
    npt = len(x)

    # Sort
    xsort = np.sort(x)
    perx = (np.arange(npt)+1) / npt

    f = interp1d(perx, xsort)

    frac = (1.-per) / 2.

    # Fill
    xper = np.zeros(2)
    try:
        xper[0] = f( frac )
    except ValueError:
        xper[0] = np.min(x)

    try:
        xper[1] = f( 1.-frac )
    except ValueError:
        xper[1] = np.max(x)

    # Return
    return xper


