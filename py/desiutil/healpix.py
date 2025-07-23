"""
================
desiutil.healpix
================

Utilities for working with healpix tiling, including unique pixel
encoding both nside,healpix into a single integer:

    uniqpix = healpix + 4*nside**2

See Section 3.2 of the `HEALpix Primer <https://healpix.sourceforge.io/pdf/intro.pdf>`_
for further information about the unique pixel identifier scheme.

DESI uses nested healpixels (not ring), with coordinates ra,dec in degrees.
"""

import os, sys
import numpy as np
import healpy

def radec2hpix(nside, ra, dec):
    """Convert nside, ra, dec in degrees to nested healpixel number

    Args:
        nside (int or array of int): healpixel nside (power of 2)
        ra (float or array of float): Right Ascension (degrees)
        dec (float or array of float): Declination (degrees)

    Returns:
        healpixel number(s)
    """
    return healpy.ang2pix(nside, ra, dec, lonlat=True, nest=True)

def radec2upix(nside, ra, dec):
    """Convert nside, ra, dec in degrees to nested unique pixel number

    Args:
        nside (int or array of int): healpixel nside (power of 2)
        ra (float or array of float): Right Ascension (degrees)
        dec (float or array of float): Declination (degrees)

    Returns:
        uniquepixel(s)
    """
    hpix = radec2hpix(nside, ra, dec)
    return hpix2upix(nside, hpix)

def hpix2upix(nside, hpix):
    """Convert nside,healpix into unique pixel

    Args:
        nside (int or array of int): healpixel nside (power of 2)
        hpix (int or array of int): healpixel number

    Returns:
        uniquepixel(s)
    """
    return hpix + 4*nside**2

def upix2hpix(upix):
    """Decode unique pixel upix into nside and healpixel

    Args:
        upix (int or array of int): encoded unique pixel(s)

    Returns (nsides, healpixels)
    """
    nside = 2**( (np.log2(upix//4)/2).astype(int) )
    hpix = upix - 4 * nside**2

    return nside, hpix

def partition_radec(ra, dec, nmax):
    """Partition `ra,dec` arrays into nested unique pixels with at most `nmax` elements each

    Args:
        ra (array of float): Right Ascension (degrees)
        dec (array of float): Declination (degrees)
        nmax (int): maximum entries per unique pixel

    Returns:
        uniqpixels (array of same length as `ra` and `dec`)

    Partitions ra,dec elements into healpix, recursively splitting
    healpixels with more than nmax elements into smaller healpix at
    larger nside, until all healpix have nmax or fewer elements.
    Returns corresponding (nside,healpix) encoded into unique pixels.
    """

    #- First calculate upix at nside=1
    order = 0
    nside = 2**order
    hpix = radec2hpix(nside, ra, dec)
    upix = hpix2upix(nside, hpix)

    #- then iteratively split large pixels into higher nside (smaller pixels)
    #- until all pixels have fewer than nmax entries.
    for order in range(1,12):
        upix_values, target_per_upix = np.unique(upix, return_counts=True)
        too_many = (target_per_upix > nmax)
        if np.any(too_many):
            ii = np.isin(upix, upix_values[too_many])
            nside = 2**order
            print(f'{np.sum(too_many)}/{len(too_many)} upix with {np.sum(ii)} targets are too dense; splitting those from nside={nside//2} to {nside}')
            hpix = radec2hpix(nside, ra[ii], dec[ii])
            upix[ii] = hpix2upix(nside, hpix)
        else:
            break

    return upix

def is_in_sorted_array(a, b):
    """
    Return bool array for if elements of array `a` are in sorted array `b`

    Note: for efficiency, this does not check that `b` is sorted
    """
    # Find the insertion points for elements of a in b
    a = np.asarray(a)
    b = np.asarray(b)
    indices = np.searchsorted(b, a)

    # Check if the elements at these indices match the elements of a
    # while avoiding overflow
    return (indices < len(b)) & (b[indices%len(b)] == a)

def find_upix(ra, dec, available_upix):
    """find which nested unique pixels cover input ra,dec values

    Args:
        ra (array of float): Right Ascension (degrees)
        dec (array of float): Declination (degrees)
        available_upix (int array): unique pixels

    Returns:
        uniqpix array for each ra,dec element. 0 if not in available_upix.

    Input ra,dec can map to multiple healpix at different nside, and thus
    multiple unique pixel values. Given array of which `available_upix` values
    are actually used, this function finds which `uniqpix` values to use for
    each ra,dec.
    """

    #- Handle scalar or vector input
    scalar_input = np.isscalar(ra)
    ra = np.atleast_1d(ra)
    dec = np.atleast_1d(dec)
    assert len(ra) == len(dec)

    #- Confirm that available_upix is sorted and unique
    if not np.all(np.diff(available_upix) > 0):
        available_upix = np.unique(available_upix)

    #- Output array to fill
    result_upix = np.zeros(len(ra), dtype=int)
    not_found = np.ones(len(ra), dtype=bool)

    #- Loop over possible nsides, testing if ra,dec values are in
    #- available_upix at that nside.  Do this in descending order
    #- so that radec2hpix is only calculated once (slow).

    available_nside = np.unique( upix2hpix(available_upix)[0] )
    assert available_nside[0] >= 1
    nside = available_nside[-1]  # max nside
    hpix = radec2hpix(nside, ra, dec)
    while nside >= available_nside[0]:
        if nside in available_nside:
            #- Calculate uniq pixels only for targets not yet found
            upix = hpix2upix(nside, hpix[not_found])

            #- keep if this upix is indeed in the input upix
            keep = is_in_sorted_array(upix, available_upix)

            #- Update output array for whether this has been found
            result_upix[not_found] = upix * keep  #- keep=False elements remain 0
            not_found[not_found] = ~keep          #- not_found elements are now found

        #- done with this nside, move to next smaller nside
        nside = nside//2
        hpix = hpix//4    #- much faster than recalculating radec2hpix

    #- Return scalar or vector output depending upon ra/dec input
    if scalar_input:
        return result_upix[0]
    else:
        return result_upix


