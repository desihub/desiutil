# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
===============
desiutils.stats
===============

Just contains a dead-simple wrapper on numpy.percentile.
"""
from __future__ import (print_function, absolute_import, division,
                        unicode_literals)

import numpy as np


def perc(x, per=68.2):
    """Calculate the percentile bounds of a distribution,
    *i.e.* for per=68, the code returns the upper and lower bounds
    that encompass 68 percent of the distribution.

    Uses simple interpolation.

    Parameters
    ----------
    x : float
        numpy array of values
    per : float, optional
        Percentile for the calculation [0-100]

    Returns
    -------
    array
        Value at lower, value at upper
    """
    #
    return np.percentile(x, [50-per/2.0, 50+per/2.0])
