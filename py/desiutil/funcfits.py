# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
==================
desiutils.funcfits
==================

Module for fitting simple functions to 1D arrays

J. Xavier Prochaska, UC Santa Cruz
Fall 2015
"""
from __future__ import (print_function, absolute_import, division,
                        unicode_literals)

import numpy as np
import copy
import warnings


def func_fit(x, y, func, deg, xmin=None, xmax=None, w=None, **kwargs):
    """Simple function fit to 2 arrays.

    Modified code originally from Ryan Cooke (PYPIT).

    Parameters
    ----------
    x : ndarray
    y : ndarray
    func : str
        Name of the fitting function:  polynomial, legendre, chebyshev.
    deg : int or dict
        Order of the fit.
    xmin : float, optional
        Minimum value in the array (or the left limit for a
        legendre/chebyshev polynomial).
    xmax : float, optional
        Maximum value in the array (or the left limit for a
        legendre/chebyshev polynomial).
    w : ndarray, optional
        Weights to be used in the fitting (weights = 1/sigma).

    Returns
    -------
    dict
        dict describing the Fit including the coefficients.
    """
    # Normalize
    if xmin is None or xmax is None:
        if np.size(x) == 1:
            xmin, xmax = -1.0, 1.0
        else:
            xmin, xmax = np.min(x), np.max(x)
    xv = 2.0 * (x-xmin)/(xmax-xmin) - 1.0
    # Fit
    if func == "polynomial":
        fit = np.polynomial.polynomial.polyfit(xv, y, deg, w=w)
    elif func == "legendre":
        fit = np.polynomial.legendre.legfit(xv, y, deg, w=w)
    elif func == "chebyshev":
        fit = np.polynomial.chebyshev.chebfit(xv, y, deg, w=w)
    else:
        raise ValueError("Fitting function '{0:s}' is not implemented yet".format(func))
    # Finish
    fit_dict = dict(coeff=fit, order=deg, func=func, xmin=xmin, xmax=xmax,
                    **kwargs)
    return fit_dict


def func_val(x, fit_dict):
    """Get values from a fit_dict.

    Modified code originally from Ryan Cooke (PYPIT).

    Parameters
    ----------
    x : ndarray

    Returns
    -------
    ndarray
        Array containing the values.
    """
    xv = 2.0 * (x-fit_dict['xmin'])/(fit_dict['xmax']-fit_dict['xmin']) - 1.0
    if fit_dict['func'] == "polynomial":
        return np.polynomial.polynomial.polyval(xv, fit_dict['coeff'])
    elif fit_dict['func'] == "legendre":
        return np.polynomial.legendre.legval(xv, fit_dict['coeff'])
    elif fit_dict['func'] == "chebyshev":
        return np.polynomial.chebyshev.chebval(xv, fit_dict['coeff'])
    else:
        raise ValueError("Fitting function '{0:s}' is not implemented yet".format(fit_dict['func']))


def iter_fit(xarray, yarray, func, order, weights=None, sigma=None,
             max_rej=None, maxone=True, sig_rej=3.0, initialmask=None,
             forceimask=False, xmin=None, xmax=None, niter=999, **kwargs):
    """A "robust" fit with iterative rejection is performed to the
    xarray, yarray pairs.

    Modified code originally from Ryan Cooke (PYPIT).

    Parameters
    ----------
    xarray : ndarray
        Independent variable values.
    yarray : ndarray
        Dependent variable values.
    func : str
        Name of the fitting function:  polynomial, legendre, chebyshev.
    order : int
        The order of the function to be used in the fitting.
    sigma : ndarray, optional
        Error in the yvalues.  Used only for rejection.
    weights : ndarray, optional
        Weights to be used in the fitting (weights = 1/sigma).
    maxone : bool, optional [True]
        If ``True``, only the most deviant point in a given iteration will
        be removed.
    sig_rej : float, optional [3.0]
        Confidence interval for rejection.
    max_rej : int, optional [None]
        Maximum number of points to reject.
    initialmask : ndarray
        A mask can be supplied as input, these values will be masked for
        the first iteration. 1 = value masked.
    forceimask : bool, optional [False]
        If ``True``, the initialmask will be forced for all iterations.
    niter : int, optional [999]
        Maximum number of iterations.
    xmin : float
        Minimum value in the array (or the left limit for a
        legendre/chebyshev polynomial).
    xmax : float
        Maximum value in the array (or the right limit for a
        legendre/chebyshev polynomial).

    Returns
    -------
    tuple
        The tuple contains a dict containing the fit and a mask array
        containing masked values.
    """
    # Setup the initial mask
    if initialmask is None:
        mask = np.zeros(xarray.size, dtype=np.int)
        if forceimask:
            warnings.warn("Initial mask cannot be enforced -- no initital mask supplied")
            forceimask = False
    else:
        mask = initialmask.copy()
    # Avoid zero or negative weights
    if weights is not None:
        mask[weights <= 0.] = 1
    mskcnt = np.sum(mask)
    imskcnt = copy.copy(mskcnt)
    # Iterate, and mask out new values on each iteration
    iiter = 0
    while True:
        iiter += 1
        if iiter > niter:
            warnings.warn("Reached maximum number of iterations")
            break
        # Mask
        w = np.where(mask == 0)
        xfit = xarray[w]
        yfit = yarray[w]
        # Fit
        dfit = func_fit(xfit, yfit, func, order, xmin=xmin, xmax=xmax,
                        **kwargs)
        yrng = func_val(xarray, dfit)
        # Reject
        sigmed = 1.4826*np.median(np.abs(yfit-yrng[w]))
        # Check number of parameters
        if xarray.size-np.sum(mask) <= order+2:
            warnings.warn("More parameters than data points - fit might be undesirable")
            break  # More data was masked than allowed by order
        if maxone:  # Only remove the most deviant point
            if sigma is not None:
                tst = np.abs(yarray[w]-yrng[w])/sigma[w]
                m = np.argmax(tst)
                if tst[m] > sig_rej:
                    mask[w[0][m]] = 1
            else:
                tst = np.abs(yarray[w]-yrng[w])
                m = np.argmax(tst)
                if tst[m] > sig_rej*sigmed:
                    mask[w[0][m]] = 1
        else:
            if forceimask:
                if sigma is not None:
                    w = np.where((np.abs(yarray-yrng) > sig_rej*sigma) |
                                 (initialmask == 1))
                else:
                    w = np.where((np.abs(yarray-yrng) > sig_rej*sigmed) |
                                 (initialmask == 1))
            else:
                if sigma is not None:
                    w = np.where(np.abs(yarray-yrng) > sig_rej*sigma)
                else:
                    w = np.where(np.abs(yarray-yrng) > sig_rej*sigmed)
            mask[w] = 1
        if mskcnt == np.sum(mask):
            break   # No new values have been included in the mask
        if max_rej is not None:
            if mskcnt-imskcnt > max_rej:
                break
        mskcnt = np.sum(mask)
        w = np.where(mask == 0)
    # Final fit
    xfit = xarray[w]
    yfit = yarray[w]
    fdict = func_fit(xfit, yfit, func, order, xmin=xmin, xmax=xmax, **kwargs)
    return fdict, mask
