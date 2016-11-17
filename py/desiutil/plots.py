# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
===============
desiutils.plots
===============

Module for code plots.
"""
from __future__ import (print_function, absolute_import, division,
                        unicode_literals)

import numpy as np

try:
    basestring
except NameError:  # For Python 3
    basestring = str


def plot_slices(x, y, x_lo, x_hi, y_cut, num_slices=5, min_count=100, axis=None,
                set_ylim_from_stats=True):
    """Scatter plot with 68, 95 percentiles superimposed in slices.
    Modified from code written by D. Kirkby

    Requires that the matplotlib package is installed.

    Parameters
    ----------
    x : array of :class:`float`
        X-coordinates to scatter plot.  Points outside [x_lo, x_hi] are
        not displayed.
    y : array of :class:`float`
        Y-coordinates to scatter plot.  Y values are assumed to be roughly
        symmetric about zero.
    x_lo : :class:`float`
        Minimum value of `x` to plot.
    x_hi : :class:`float`
        Maximum value of `x` to plot.
    y_cut : :class:`float`
        The target maximum value of :math:`|y|`.  A dashed line at this value
        is added to the plot, and the vertical axis is clipped at
        :math:`|y|` = 1.25 * `y_cut` (but values outside this range are
        included in the percentile statistics).
    num_slices : :class:`int`, optional
        Number of equally spaced slices to divide the interval [x_lo, x_hi]
        into.
    min_count : :class:`int`, optional
        Do not use slices with fewer points for superimposed percentile
        statistics.
    axis : :class:`matplotlib.axes.Axes`, optional
        Uses the current axis if this is not set.
    set_ylim_from_stats : :class:`bool`, optional
        Set ylim of plot from 95% stat.

    Returns
    -------
    :class:`matplotlib.axes.Axes`
        The Axes object used in the plot.
    """
    import matplotlib.pyplot as plt

    if axis is None:
        axis = plt.gca()

    x_bins = np.linspace(x_lo, x_hi, num_slices + 1)
    x_i = np.digitize(x, x_bins) - 1
    limits = []
    counts = []
    for s in range(num_slices):
        # Calculate percentile statistics for ok fits.
        y_slice = y[(x_i == s)]
        counts.append(len(y_slice))
        if counts[-1] > 0:
            limits.append(np.percentile(y_slice, (2.5, 16, 50, 84, 97.5)))
        else:
            limits.append((0., 0., 0., 0., 0.))
    limits = np.array(limits)
    counts = np.array(counts)

    # Plot scatter of all fits.
    axis.scatter(x, y, s=15, marker='.', lw=0, color='b', alpha=0.5)
    #axis.scatter(x[~ok], y[~ok], s=15, marker='x', lw=0, color='k', alpha=0.5)

    # Plot quantiles in slices with enough fits.
    stepify = lambda y: np.vstack([y, y]).transpose().flatten()
    y_m2 = stepify(limits[:, 0])
    y_m1 = stepify(limits[:, 1])
    y_med = stepify(limits[:, 2])
    y_p1 = stepify(limits[:, 3])
    y_p2 = stepify(limits[:, 4])
    xstack = stepify(x_bins)[1:-1]
    max_yr, max_p2, min_m2 = 0., -1e9, 1e9
    for i in range(num_slices):
        s = slice(2 * i, 2 * i + 2)
        if counts[i] >= min_count:
            axis.fill_between(
                xstack[s], y_m2[s], y_p2[s], alpha=0.15, color='red')
            axis.fill_between(
                xstack[s], y_m1[s], y_p1[s], alpha=0.25, color='red')
            axis.plot(xstack[s], y_med[s], 'r-', lw=2.)
            # For ylim
            max_yr = max(max_yr, np.max(y_p2[s]-y_m2[s]))
            max_p2 = max(max_p2, np.max(y_p2[s]))
            min_m2 = min(min_m2, np.min(y_m2[s]))

    # xlim
    xmin,xmax = np.min(x), np.max(x)
    axis.set_xlim(np.min(x)-(xmax-xmin)*0.02, np.max(x)+(xmax-xmin)*0.02)

    # ylim
    if set_ylim_from_stats:
        axis.set_ylim(min_m2-max_yr/2., max_p2+max_yr/2.)

    # Plot cut lines.
    axis.axhline(+y_cut, ls=':', color='k')
    axis.axhline(0., ls='-', color='k')
    axis.axhline(-y_cut, ls=':', color='k')

    return axis
