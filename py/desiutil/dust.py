# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
=============
desiutil.dust
=============

Get :math:`E(B-V)` values from the `Schlegel, Finkbeiner & Davis (1998; SFD98)`_ dust map.

.. _`Schlegel, Finkbeiner & Davis (1998; SFD98)`: http://adsabs.harvard.edu/abs/1998ApJ...500..525S.
"""
import os
import numpy as np
from astropy.io.fits import getdata
from astropy.coordinates import SkyCoord
from astropy import units as u
from .log import get_logger
log = get_logger()

def extinction_total_to_selective_ratio(band, photsys) :
    """Return the linear coefficient R_B = A(B)/E(B-V) where
    A(B) = -2.5*log10(transmission in B band), for band B in 'G','R' or 'Z',
    the optical bands of the legacy surveys. photsys = 'N' or 'S' specifies
    the survey (BASS+MZLS or DECALS).  E(B-V) is interpreted as SFD.

    Args:
        band : 'G', 'R' or 'Z'
        photsys : 'N' or 'S'

    Returns:
        scalar, total extinction A(band) = -2.5*log10(transmission(band))
    """

    # fitted from the imaging data (using fibermaps of 2020/03/15)
    R={"G_N":3.2140,
       "R_N":2.1650,
       "Z_N":1.2110,
       "G_S":3.2829,
       "R_S":2.1999,
       "Z_S":1.2150}
    assert(band.upper() in ["G","R","Z"])
    assert(photsys.upper() in ["N","S"])
    return R["{}_{}".format(band.upper(),photsys.upper())]

def mwdust_transmission(ebv, band, photsys):
    """Convert SFD E(B-V) value to dust transmission 0-1 for band and photsys

    Args:
        ebv (float or array-like): SFD E(B-V) value(s)
        band (str): 'G', 'R', or 'Z'
        photsys (str or array of str): 'N' or 'S' imaging surveys photo system

    Returns:
        scalar or array (same as ebv input), Milky Way dust transmission 0-1

    If `photsys` is an array, `ebv` must also be array of same length.
    However, `ebv` can be an array with a str `photsys`.
    """
    if isinstance(photsys, str):
        r_band = extinction_total_to_selective_ratio(band, photsys)
        a_band = r_band * ebv
        transmission = 10**(-a_band / 2.5)
        return transmission
    else:
        photsys = np.asarray(photsys)
        if np.isscalar(ebv):
            raise ValueError('array photsys requires array ebv')
        if len(ebv) != len(photsys):
            raise ValueError('len(ebv) {} != len(photsys) {}'.format(
                len(ebv), len(photsys)))

        transmission = np.zeros(len(ebv))
        for p in np.unique(photsys):
            ii = (photsys == p)
            r_band = extinction_total_to_selective_ratio(band, p)
            a_band = r_band * ebv[ii]
            transmission[ii] = 10**(-a_band / 2.5)

        return transmission

def ext_odonnell(wave, Rv=3.1):
    """Return extinction curve from Odonnell (1994), defined in the wavelength
    range [3030,9091] Angstroms.  Outside this range, use CCM (1989).

    Args:
        wave : 1D array of vacuum wavelength [Angstroms]
        Rv   : Value of R_V (scalar); default is 3.1

    Returns:
        1D array of A(lambda)/A(V)
    """

    # direct python translation of idlutils/pro/dust/ext_odonnell.pro

    A = np.zeros(wave.shape)
    xx = 10000. / wave

    optical_waves = (xx >= 1.1) & (xx <= 3.3)
    other_waves = (xx < 1.1) | (xx > 3.3)

    if np.sum(optical_waves) > 0:
        yy = xx[optical_waves] - 1.82
        afac = (1.0 + 0.104*yy - 0.609*yy**2 + 0.701*yy**3 + 1.137*yy**4 -
                1.718*yy**5 - 0.827*yy**6 + 1.647*yy**7 - 0.505*yy**8)
        bfac = (1.952*yy + 2.908*yy**2 - 3.989*yy**3 - 7.985*yy**4 +
                11.102*yy**5 + 5.491*yy**6 - 10.805*yy**7 + 3.347*yy**8)
        A[optical_waves] = afac + bfac / Rv
    if np.sum(other_waves) > 0:
        A[other_waves] = ext_ccm(wave[other_waves], Rv=Rv)

    return A


def ext_ccm(wave, Rv=3.1):
    """Return extinction curve from CCM (1989), defined in the wavelength
    range [1250,33333] Angstroms.

    Args:
        wave : 1D array of vacuum wavelength [Angstroms]
        Rv   : Value of R_V (scalar); default is 3.1

    Returns:
        1D array of A(lambda)/A(V)
    """

    # direct python translation of idlutils/pro/dust/ext_ccm.pro
    # numeric values checked with other implementation

    A = np.zeros(wave.shape)
    xx = 10000. / wave

    # Limits for CCM fitting function
    qLO = (xx > 8.0)                   # No data, lambda < 1250 Ang
    qUV = (xx > 3.3) & (xx <= 8.0)     # UV + FUV
    qOPT = (xx > 1.1) & (xx <= 3.3)    # Optical/NIR
    qIR = (xx > 0.3) & (xx <= 1.1)     # IR
    qHI = (xx <= 0.3)                  # No data, lambda > 33,333 Ang

    # For lambda < 1250 Ang, arbitrarily return Alam=5
    if np.sum(qLO) > 0:
        A[qLO] = 5.0

    if np.sum(qUV) > 0:
        xt = xx[qUV]
        afac = 1.752 - 0.316*xt - 0.104 / ((xt - 4.67)**2 + 0.341)
        bfac = -3.090 + 1.825*xt + 1.206 / ((xt - 4.62)**2 + 0.263)

        qq = (xt >= 5.9) & (xt <= 8.0)
        if np.sum(qq) > 0:
            Fa = -0.04473*(xt[qq]-5.9)**2 - 0.009779*(xt[qq]-5.9)**3
            Fb = 0.2130*(xt[qq]-5.9)**2 + 0.1207*(xt[qq]-5.9)**3
            afac[qq] += Fa
            bfac[qq] += Fb

        A[qUV] = afac + bfac / Rv

    if np.sum(qOPT) > 0:
        yy = xx[qOPT] - 1.82
        afac = (1.0 + 0.17699*yy - 0.50447*yy**2 - 0.02427*yy**3 +
                0.72085*yy**4 + 0.01979*yy**5 - 0.77530*yy**6 + 0.32999*yy**7)
        bfac = (1.41338*yy + 2.28305*yy**2 + 1.07233*yy**3 -
                5.38434*yy**4 - 0.62251*yy**5 + 5.30260*yy**6 - 2.09002*yy**7)
        A[qOPT] = afac + bfac / Rv

    if np.sum(qIR) > 0:
        yy = xx[qIR]**1.61
        afac = 0.574*yy
        bfac = -0.527*yy
        A[qIR] = afac + bfac / Rv

    # For lambda > 33,333 Ang, arbitrarily extrapolate the IR curve
    if np.sum(qHI) > 0:
        yy = xx[qHI]**1.61
        afac = 0.574*yy
        bfac = -0.527*yy
        A[qHI] = afac + bfac / Rv

    return A


# The SFDMap and _Hemisphere classes and the _bilinear_interpolate and ebv
# functions below were copied on Nov/20/2016 from
# https://github.com/kbarbary/sfdmap/ commit: bacdbbd
# which was originally Licensed under an MIT "Expat" license:
#
# Copyright (c) 2016 Kyle Barbary
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


def _bilinear_interpolate(data, y, x):
    """Map a two-dimensional integer pixel-array at float coordinates.

    Parameters
    ----------
    data : :class:`~numpy.ndarray`
        Pixelized array of values.
    y : :class:`float` or :class:`~numpy.ndarray`
        y coordinates (each integer y is a row) of
        location in pixel-space at which to interpolate.
    x : :class:`float` or :class:`~numpy.ndarray`
        x coordinates (each integer x is a column) of
        location in pixel-space at which to interpolate.

    Returns
    -------
    :class:`float` or :class:`~numpy.ndarray`
        Interpolated data values at the passed locations.

    Notes
    -----
    Taken in full from https://github.com/kbarbary/sfdmap/
    """
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

    return ((1.0 - xw) * (1.0 - yw) * data[y0, x0] +
            xw * (1.0-yw) * data[y0, x1] +
            (1.0 - xw) * yw * data[y1, x0] +
            xw * yw * data[y1, x1])


class _Hemisphere(object):
    """Represents one of the hemispheres (in a single file).

    Parameters
    ----------
    fname : :class:`str`
        File name containing one hemisphere of the dust map.
    scaling : :class:`float`
        Multiplicative factor by which to scale the dust map.

    Attributes
    ----------
    data : :class:`~numpy.ndarray`
        Pixelated array of dust map values.
    crpix1, crpix2 : :class:`float`
        World Coordinate System: Represent the 1-indexed
        X and Y pixel numbers of the poles.
    lam_scal : :class:`int`
        Number of pixels from b=0 to b=90 deg.
    lam_nsgp : :class:`int`
        +1 for the northern hemisphere, -1 for the south.

    Notes
    -----
    Taken in full from https://github.com/kbarbary/sfdmap/
    """
    def __init__(self, fname, scaling):
        self.data, header = getdata(fname, header=True)
        self.data *= scaling
        self.crpix1 = header['CRPIX1']
        self.crpix2 = header['CRPIX2']
        self.lam_scal = header['LAM_SCAL']
        self.sign = header['LAM_NSGP']  # north = 1, south = -1

    def ebv(self, l, b, interpolate):
        """Project Galactic longitude/latitude to lambert pixels (See SFD98).

        Parameters
        ----------
        l, b : :class:`numpy.ndarray`
            Galactic longitude and latitude.
        interpolate : :class:`bool`
            If ``True`` use bilinear interpolation to obtain values.

        Returns
        -------
        :class:`~numpy.ndarray`
            Reddening values.
        """
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
    mapdir : :class:`str`, optional, defaults to :envvar:`DUST_DIR`+``/maps``.
        Directory in which to find dust map FITS images, named
        ``SFD_dust_4096_ngp.fits`` and ``SFD_dust_4096_sgp.fits``.
        If not specified, the map directory is derived from the value of
        the :envvar:`DUST_DIR` environment variable, otherwise an empty
        string is used.
    north, south : :class:`str`, optional
        Names of north and south galactic pole FITS files. Defaults are
        ``SFD_dust_4096_ngp.fits`` and ``SFD_dust_4096_sgp.fits``
        respectively.
    scaling : :class:`float`, optional, defaults to 1
        Scale all E(B-V) map values by this multiplicative factor.
        Pass scaling=0.86 for the recalibration from
        `Schlafly & Finkbeiner (2011) <http://adsabs.harvard.edu/abs/2011ApJ...737..103S)>`_.

    Notes
    -----
    Modified from https://github.com/kbarbary/sfdmap/
    """
    def __init__(self, mapdir=None, north="SFD_dust_4096_ngp.fits",
                 south="SFD_dust_4096_sgp.fits", scaling=1.):

        if mapdir is None:
            dustdir = os.environ.get('DUST_DIR')
            if dustdir is None:
                log.critical('Pass mapdir or set $DUST_DIR')
                raise ValueError('Pass mapdir or set $DUST_DIR')
            else:
                mapdir = os.path.join(dustdir, 'maps')

        if not os.path.exists(mapdir):
            log.critical('Dust maps not found in directory {}'.format(mapdir))
            raise ValueError('Dust maps not found in directory {}'.format(mapdir))

        self.mapdir = mapdir

        # don't load maps initially
        self.fnames = {'north': north, 'south': south}
        self.hemispheres = {'north': None, 'south': None}

        self.scaling = scaling

    def ebv(self, *args, **kwargs):
        """Get E(B-V) value(s) at given coordinate(s).

        Parameters
        ----------
        coordinates : :class:`~astropy.coordinates.SkyCoord` or :class:`~numpy.ndarray`
            If one argument is passed, assumed to be an :class:`~astropy.coordinates.SkyCoord`
            instance, in which case the ``frame`` and ``unit`` keyword arguments are
            ignored. If two arguments are passed, they are treated as
            ``latitute, longitude`` (can be scalars or arrays or a tuple), in which
            case the frame and unit are taken from the passed keywords.
        frame : :class:`str`, optional, defaults to ``'icrs'``
            Coordinate frame, if two arguments are passed. Allowed values are any
            :class:`~astropy.coordinates.SkyCoord` frame, and ``'fk5j2000'`` and ``'j2000'``.
        unit : :class:`str`, optional, defaults to ``'degree'``
            Any :class:`~astropy.coordinates.SkyCoord` unit.
        interpolate : :class:`bool`, optional, defaults to ``True``
            Interpolate between the map values using bilinear interpolation.

        Returns
        -------
        :class:`~numpy.ndarray`
            Specific extinction E(B-V) at the given locations.

        Notes
        -----
        Modified from https://github.com/kbarbary/sfdmap/
        """
        # collect kwargs
        frame = kwargs.get('frame', 'icrs')
        unit = kwargs.get('unit', 'degree')
        interpolate = kwargs.get('interpolate', True)

        # ADM convert to a frame understood by SkyCoords
        # ADM (for backwards-compatibility)
        if frame in ('fk5j2000', 'j2000'):
            frame = 'fk5'

        # compatibility: treat single argument 2-tuple as (RA, Dec)
        if (
                (len(args) == 1) and (type(args[0]) is tuple)
                and (len(args[0]) == 2)
        ):
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

        # ADM extract Galactic coordinates from astropy
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
    """Convenience function, equivalent to ``SFDMap().ebv(*args)``.
    """

    m = SFDMap(mapdir=kwargs.get('mapdir', None),
               north=kwargs.get('north', "SFD_dust_4096_ngp.fits"),
               south=kwargs.get('south', "SFD_dust_4096_sgp.fits"),
               scaling=kwargs.get('scaling', 1.))
    return m.ebv(*args, **kwargs)
