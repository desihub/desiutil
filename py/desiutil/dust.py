# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
#
# ORIGINAL LICENSE:
# Copied on Nov/20/2016 from https://github.com/kbarbary/sfdmap/ commit: bacdbbd

# Licensed under an MIT "Expat" license

# Copyright (c) 2016 Kyle Barbary

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
=============
desiutil.dust
=============

Get E(B-V) values from the Schlegel, Finkbeiner & Davis (1998) dust map.
See, e.g.: http://adsabs.harvard.edu/abs/1998ApJ...500..525S for SFD98.
"""

import os
import numpy as np
from astropy.io.fits import getdata
from astropy.coordinates import SkyCoord
from astropy import units as u

# -----------------------------------------------------------------------------
# bilinear interpolation (because scipy.ndimage.map_coordinates is really slow
# for this)

def _bilinear_interpolate(data, y, x):
    yfloor = np.floor(y)
    xfloor = np.floor(x)
    yw = y - yfloor
    xw = x - xfloor

    # pixel locations
    y0 = yfloor.astype(np.int)
    y1 = y0 + 1
    x0 = xfloor.astype(np.int)
    x1 = x0 + 1

    # clip locations out of range
    ny, nx = data.shape
    y0 = np.maximum(y0, 0)
    y1 = np.minimum(y1, ny-1)
    x0 = np.maximum(x0, 0)
    x1 = np.minimum(x1, nx-1)

    return ((1.0-xw) * (1.0-yw) * data[y0, x0] +
            xw       * (1.0-yw) * data[y0, x1] +
            (1.0-xw) * yw       * data[y1, x0] +
            xw       * yw       * data[y1, x1])


# -----------------------------------------------------------------------------

class _Hemisphere(object):
    """Represents one of the hemispheres (in a single fle)"""

    def __init__(self, fname, scaling):
        self.data, header = getdata(fname, header=True)
        self.data *= scaling
        self.crpix1 = header['CRPIX1']
        self.crpix2 = header['CRPIX2']
        self.lam_scal = header['LAM_SCAL']
        self.sign = header['LAM_NSGP']  # north = 1, south = -1

    def ebv(self, l, b, interpolate):
        # Project from galactic longitude/latitude to lambert pixels.
        # (See SFD98 or SFD data FITS header).
        x = (self.crpix1 - 1.0 +
             self.lam_scal * np.cos(l) *
             np.sqrt(1.0 - self.sign * np.sin(b)))
        y = (self.crpix2 - 1.0 -
             self.sign * self.lam_scal * np.sin(l) *
             np.sqrt(1.0 - self.sign * np.sin(b)))

        # Get map values at these pixel coordinates.
        if interpolate:
            return _bilinear_interpolate(self.data, y, x)
        else:
            x = np.round(x).astype(np.int)
            y = np.round(y).astype(np.int)

            # some valid coordinates are right on the border (e.g., x/y = 4096)
            x = np.clip(x, 0, self.data.shape[1]-1)
            y = np.clip(y, 0, self.data.shape[0]-1)
            return self.data[y, x]


class SFDMap(object):
    """Map of E(B-V) from Schlegel, Finkbeiner and Davis (1998).

    Use this class for repeated retrieval of E(B-V) values when
    there is no way to retrieve all the values at the same time: It keeps
    a reference to the FITS data from the maps so that each FITS image
    is read only once.

    Parameters
    ----------

    mapdir : str, optional

        Directory in which to find dust map FITS images, named
        ``SFD_dust_4096_ngp.fits`` and ``SFD_dust_4096_sgp.fits`` by
        default. If not specified, the value of the ``DUST_DIR``
        environment variable is used, otherwise an empty string is
        used.

    north, south : str, optional

        Names of north and south galactic pole FITS files. Defaults are
        ``SFD_dust_4096_ngp.fits`` and ``SFD_dust_4096_sgp.fits``
        respectively.

    scaling : float, optional
        Scale all E(B-V) map values by this factor. Default is 1.,
        corresponding to no recalibration. Pass scaling=0.86 for the
        recalibration from Schlafly & Finkbeiner (2011).
    """

    def __init__(self, mapdir=None, north="SFD_dust_4096_ngp.fits",
                 south="SFD_dust_4096_sgp.fits", scaling=1.):

        if mapdir is None:
            mapdir = os.environ.get('DUST_DIR')
        self.mapdir = mapdir

        # don't load maps initially
        self.fnames = {'north': north, 'south': south}
        self.hemispheres = {'north': None, 'south': None}

        self.scaling = scaling

    def ebv(self, *args, **kwargs):
        """Get E(B-V) value(s) at given coordinate(s).

        Parameters
        ----------
        coordinates or ra, dec: SkyCoord or numpy.ndarray
            If one argument is passed, assumed to be an (ra,dec) tuple 
             or an `astropy.coordinates.SkyCoords` instance. In the
            `astropy.coordinates.SkyCoords` case
            the ``frame`` and ``unit`` keyword arguments are
            ignored. If two arguments are passed, they are treated as
            ``latitute, longitude`` (can be scalars or arrays).  In
            the two argument case, the frame and unit is taken from
            the keywords.
        frame : {'icrs', 'fk5j2000', 'galactic'}, optional
            Coordinate frame, if two arguments are passed. Default is
            ``'icrs'``.
        unit : {'degree', 'radian'}, optional
            Unit of coordinates, if two arguments are passed. Default
            is ``'degree'``.
        interpolate : bool, optional
            Interpolate between the map values using bilinear interpolation.
            Default is True.

        Returns
        -------
        `~numpy.ndarray`
            Specific extinction E(B-V) at the given locations.

        """

        # collect kwargs
        frame = kwargs.get('frame', 'icrs')
        unit = kwargs.get('unit', 'degree')
        interpolate = kwargs.get('interpolate', True)

        #ADM convert to a frame understood by SkyCoords
        #ADM (for backwards-compatibility)
        if frame in ('fk5j2000', 'j2000'):
            frame = 'fk5'

        # compatibility: treat single argument 2-tuple as (RA, Dec)
        if ((len(args) == 1) and (type(args[0]) is tuple) 
            and (len(args[0]) == 2)):
            args = args[0]

        if len(args) == 1:
            # treat object as already an astropy.coordinates.SkyCoords
            try:
                c = args[0]
            except AttributeError:
                raise ValueError("single argument must be "
                                 "astropy.coordinates.SkyCoord")

        elif len(args) == 2:
            lat, lon = args
            c = SkyCoord(lat, lon, unit=unit, frame=frame)

        else:
            raise ValueError("too many arguments")

        #ADM extract Galactic coordinates from astropy
        l, b = c.galactic.l.radian, c.galactic.b.radian

        # Check if l, b are scalar. If so, convert to 1-d arrays.
        # ADM use numpy.atleast_1d. Store whether the
        # ADM passed values were scalars or not
        return_scalar = not np.atleast_1d(l) is l
        l, b = np.atleast_1d(l), np.atleast_1d(b)

        # Initialize return array
        values = np.empty_like(l)

        # Treat north (b>0) separately from south (b<0).
        for pole, mask in (('north', b >= 0), ('south', b < 0)):
            if not np.any(mask):
                continue

            # Initialize hemisphere if it hasn't already been done.
            if self.hemispheres[pole] is None:
                fname = os.path.join(self.mapdir, self.fnames[pole])
                self.hemispheres[pole] = _Hemisphere(fname, self.scaling)

            values[mask] = self.hemispheres[pole].ebv(l[mask], b[mask],
                                                      interpolate)

        if return_scalar:
            return values[0]
        else:
            return values

    def __repr__(self):
        return ("SFDMap(mapdir={!r}, north={!r}, south={!r}, scaling={!r})"
                .format(self.mapdir, self.fnames['north'],
                        self.fnames['south'], self.scaling))


def ebv(*args, **kwargs):
    """Convenience function, equivalent to ``SFDMap().ebv(*args)``"""

    m = SFDMap(mapdir=kwargs.get('mapdir', None),
               north=kwargs.get('north', "SFD_dust_4096_ngp.fits"),
               south=kwargs.get('south', "SFD_dust_4096_sgp.fits"),
               scaling=kwargs.get('scaling', 1.))
    return m.ebv(*args, **kwargs)
