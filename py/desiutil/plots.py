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

import os

import numpy as np
import numpy.ma

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


def prepare_data(data, mask=None, clip_lo=None, clip_hi=None):
    """Prepare array data for color mapping.

    Data is clipped and masked to be suitable for passing to matplotlib
    routines that automatically assign colors based on input values.

    If no optional parameters are specified, the input data is returned
    with an empty mask:

    >>> data = np.arange(5)
    >>> prepare_data(data)
    masked_array(data = [0.0 1.0 2.0 3.0 4.0],
                 mask = [False False False False False],
           fill_value = 1e+20)

    A mask selection is propagated to the output:

    >>> prepare_data(data, data == 2)
    masked_array(data = [0.0 1.0 -- 3.0 4.0],
                 mask = [False False  True False False],
           fill_value = 1e+20)

    Values can be clipped by specifying any combination of percentiles
    (specified as strings ending with "%") and numeric values:

    >>> prepare_data(data, clip_lo='25%', clip_hi=3.5)
    masked_array(data = [1.0 1.0 2.0 3.0 3.5],
                 mask = [False False False False False],
           fill_value = 1e+20)

    Parameters
    ----------
    data : array or masked array
        Array of data values to assign colors for.
    mask : array of bool or None
        Array of bools with same shape as data, where True values indicate
        values that should be ignored when assigning colors.  When None, the
        mask of a masked array will be used or all values of an unmasked
        array will be used.
    clip_lo : float or str
        Data values below clip_lo will be clipped to the minimum color. If
        clip_lo is a string, it should end with "%" and specify a percentile
        of un-masked data to clip below.
    clip_hi : float or str
        Data values above clip_hi will be clipped to the maximum color. If
        clip_hi is a string, it should end with "%" and specify a percentile
        of un-masked data to clip above.

    Returns
    -------
    masked array
        Masked numpy array with the same shape as the input data, with any
        input mask applied (or copied from an input masked array) and values
        clipped to [clip_lo, clip_hi].
    """
    data = np.asanyarray(data)
    if mask is None:
        try:
            # Use the mask associated with a MaskedArray.
            mask = data.mask
        except AttributeError:
            # Nothing is masked by default.
            mask = np.zeros_like(data, dtype=bool)
    else:
        mask = np.asarray(mask)
        if mask.shape != data.shape:
            raise ValueError('Invalid mask shape.')
    unmasked_data = data[~mask]

    if clip_lo is None:
        clip_lo = np.min(unmasked_data)
    if clip_hi is None:
        clip_hi = np.max(unmasked_data)

    # Convert percentile clip values to absolute values.
    def get_clip(value):
        try:
            if value.endswith('%'):
                return np.percentile(unmasked_data, float(value[:-1]))
            else:
                raise ValueError('Invalid clip parameter: {0}'.format(value))
        except AttributeError:
            return float(value)

    clip_lo = get_clip(clip_lo)
    clip_hi = get_clip(clip_hi)

    clipped = numpy.ma.zeros(data.shape)
    clipped.mask = mask
    clipped[~mask] = np.clip(unmasked_data, clip_lo, clip_hi)

    return clipped


def init_sky(projection='eck4', center_longitude=60,
             galactic_plane_color='black'):
    """Initialize a basemap projection of the full sky.

    The returned Basemap object is augmented with an ``ellipse()`` method to
    support drawing ellipses or circles on the sky, which is useful for
    representing DESI tiles.

    Note that the projection uses the geographic convention that RA increases
    from left to right rather than the opposite celestial convention because
    otherwise RA labels are drawn incorrectly (see
    https://github.com/matplotlib/basemap/issues/283 for details).

    Requires that matplotlib and basemap are installed.

    Parameters
    ----------
    projection : :class: `string`, optional
        All-sky projection used for coordinate transformations. The default
        'eck4' is recommended for the reasons given `here
        <http://usersguidetotheuniverse.com/index.php/2011/03/03/
        whats-the-best-map-projection/>`__.  Other good choices are
        kav7' and 'moll'.
    center_longitude : :class: `float`, optional
        Center longitude for the plot in degrees. Default is +60, which
        avoids splitting the DESI northern and southern regions.
    galactic_plane_color : color name or None
        Draw a line representing the galactic plane using the specified
        color, or do nothing when None.

    Returns
    -------
    :class:`mpl_toolkits.basemap.Basemap`
       The Basemap object created for this plot, which can be used for
       additional projection and plotting operations.
    """
    import matplotlib
    if 'TRAVIS_JOB_ID' in os.environ:
        matplotlib.use('agg')
    from matplotlib.patches import Polygon
    from mpl_toolkits.basemap import pyproj
    from mpl_toolkits.basemap import Basemap
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    # Define a Basemap subclass with an ellipse() method.
    class BasemapWithEllipse(Basemap):
        """Code from http://stackoverflow.com/questions/8161144/
        drawing-ellipses-on-matplotlib-basemap-projections
        It adds ellipses to the class Basemap.
        """
        def ellipse(self, x0, y0, a, b, n, ax=None, **kwargs):
            """Extension to Basemap class from `basemap` to draw ellipses.

            Parameters
            ----------
            x0 : :class: `float`
                Centroid of the ellipse in the X axis.
            y0 : :class: `float`
                Centroid of the ellipse in the Y axis.
            a : :class: `float`
                Semi-major axis of the ellipse.
            b : :class: `float`
                Semi-minor axis of the ellipse.
            n : :class: `int`
                Number of points to draw the ellipse.

            Returns
            -------
            :class: `Basemap`
                It returns one Basemap ellipse at a time.
            """
            ax = kwargs.pop('ax', None) or self._check_ax()
            g = pyproj.Geod(a=self.rmajor, b=self.rminor)
            azf, azb, dist = g.inv([x0, x0],[y0, y0],[x0+a, x0],[y0, y0+b])
            tsid = dist[0] * dist[1] # a * b
            seg = [self(x0+a, y0)]
            AZ = np.linspace(azf[0], 360. + azf[0], n)
            for i, az in enumerate(AZ):
                # Skips segments along equator (Geod can't handle equatorial arcs).
                if np.allclose(0., y0) and (np.allclose(90., az) or
                    np.allclose(270., az)):
                    continue

                # In polar coordinates, with the origin at the center of the
                # ellipse and with the angular coordinate ``az`` measured from the
                # major axis, the ellipse's equation  is [1]:
                #
                #                           a * b
                # r(az) = ------------------------------------------
                #         ((b * cos(az))**2 + (a * sin(az))**2)**0.5
                #
                # Azymuth angle in radial coordinates and corrected for reference
                # angle.
                azr = 2. * np.pi / 360. * (az + 90.)
                A = dist[0] * np.sin(azr)
                B = dist[1] * np.cos(azr)
                r = tsid / (B**2. + A**2.)**0.5
                lon, lat, azb = g.fwd(x0, y0, az, r)
                x, y = self(lon, lat)

                # Add segment if it is in the map projection region.
                if x < 1e20 and y < 1e20:
                    seg.append((x, y))

            poly = Polygon(seg, **kwargs)
            ax.add_patch(poly)

            # Set axes limits to fit map region.
            self.set_axes_limits(ax=ax)

            return poly

    # Create an instance of our custom Basemap.
    m = BasemapWithEllipse(
        projection=projection, lon_0=center_longitude,
        resolution='c', celestial=False)
    m.drawmeridians(
        np.arange(0, 360, 60), labels=[0,0,1,0], labelstyle='+/-')
    m.drawparallels(
        np.arange(-90, 90, 30), labels=[1,1,0,0], labelstyle='+/-')
    m.drawmapboundary()

    # Draw the optional galactic plane.
    if galactic_plane_color is not None:
        # Generate coordinates of a line in galactic coordinates and convert
        # to equatorial coordinates.
        galactic_l = np.linspace(0, 2 * np.pi, 1000)
        galactic_plane = SkyCoord(
            l=galactic_l*u.radian, b=np.zeros_like(galactic_l)*u.radian,
            frame='galactic').fk5
        # Project to map coordinates and display.  Use a scatter plot to
        # avoid wrap-around complications.
        galactic_x, galactic_y = m(galactic_plane.ra.degree,
                                   galactic_plane.dec.degree)

        paths = m.scatter(
            galactic_x, galactic_y, marker='.', s=20, lw=0, alpha=0.75,
            c=galactic_plane_color)
        # Make sure the galactic plane stays above other displayed objects.
        paths.set_zorder(20)

    return m


def plot_healpix_map(data, mask=None, clip_lo=None, clip_hi=None,
                     cmap='viridis', colorbar=True, label=None, basemap=None):
    """Plot a healpix map using a basemap projection.

    Requires that matplotlib, basemap, and healpy are installed.

    This function is similar to :func:`plot_grid_map` but is generally slower
    at high resolution and has less elegant handling of pixels that wrap around
    in RA, which are not drawn.

    Parameters
    ----------
    data : array or masked array
        1D array of data associated with each healpix.  Must have a size that
        exactly matches the number of pixels for some NSIDE value.
    mask : array or None
        See :func:`prepare_data`.
    clip_lo : float or str
        See :func:`prepare_data`.
    clip_hi : float or str
        See :func:`prepare_data`.
    cmap : colormap name or object
        Matplotlib colormap to use for mapping data values to colors.
    colorbar : bool
        Draw a colorbar below the map when True.
    label : str or None
        Label to display under the colorbar.  Ignored unless colorbar is True.
    basemap : Basemap object or None
        Use the specified basemap or create a default basemap using
        :func:`init_sky` when None.

    Returns
    -------
    basemap
        The basemap used for the plot, which will match the input basemap
        provided, or be a newly created basemap if None was provided.
    """
    import healpy as hp
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    clipped = prepare_data(data, mask, clip_lo, clip_hi)
    if len(clipped.shape) != 1:
        raise ValueError('Invalid data array, should be 1D.')
    nside = hp.npix2nside(len(clipped))

    if basemap is None:
        basemap = init_sky()

    # Get pixel boundaries as quadrilaterals.
    corners = hp.boundaries(nside, np.arange(len(data)), step=1)
    corner_theta, corner_phi = hp.vec2ang(corners.transpose(0,2,1))
    corner_ra, corner_dec = (
        np.degrees(corner_phi), np.degrees(np.pi/2-corner_theta))
    # Convert sky coords to map coords.
    x, y = basemap(corner_ra, corner_dec)
    # Regroup into pixel corners.
    verts = np.array([x.reshape(-1,4), y.reshape(-1,4)]).transpose(1,2,0)

    # Find and mask any pixels that wrap around in RA.
    uv_verts = np.array([corner_phi.reshape(-1,4),
                         corner_theta.reshape(-1,4)]).transpose(1,2,0)
    theta_edge = np.unique(uv_verts[:, :, 1])
    phi_edge = np.radians(basemap.lonmax)
    eps = 0.1 * np.sqrt(hp.nside2pixarea(nside))
    wrapped1 = hp.ang2pix(nside, theta_edge, phi_edge - eps)
    wrapped2 = hp.ang2pix(nside, theta_edge, phi_edge + eps)
    wrapped = np.unique(np.hstack((wrapped1, wrapped2)))
    clipped.mask[wrapped] = True

    # Make the collection and add it to the plot.
    collection = PolyCollection(
        verts, array=clipped, cmap=cmap, edgecolors='none')

    plt.gca().add_collection(collection)
    plt.gca().autoscale_view()

    if colorbar:
        bar = plt.colorbar(
            collection, orientation='horizontal',
            spacing='proportional', pad=0.01, aspect=50)
        if label:
            bar.set_label(label)

    return basemap


def plot_grid_map(data, ra_edges, dec_edges, mask=None, clip_lo=None,
                  clip_hi=None, cmap='viridis', colorbar=True, label=None,
                  basemap=None):
    """Plot an array of 2D values on a grid of (RA, DEC).

    Requires that matplotlib and basemap are installed.

    This function is similar to :func:`plot_healpix_map` but is generally faster
    and has better handling of RA wrap around artifacts.

    Parameters
    ----------
    data : array or masked array
        2D array of data associated with each grid cell, with shape
        (n_ra, n_dec).
    ra_edges : array
        1D array of n_ra+1 RA grid edge values in degrees, which must span the
        full circle, i.e., ra_edges[0] == ra_edges[-1] - 360. The RA grid
        does not need to match the edges of the basemap projection, in which
        case any wrap-around cells will be duplicated on both edges.
    dec_edges : array
        1D array of n_dec+1 DEC grid edge values in degrees.  Values are not
        required to span the full range [-90, +90].
    mask : array or None
        See :func:`prepare_data`.
    clip_lo : float or str
        See :func:`prepare_data`.
    clip_hi : float or str
        See :func:`prepare_data`.
    cmap : colormap name or object
        Matplotlib colormap to use for mapping data values to colors.
    colorbar : bool
        Draw a colorbar below the map when True.
    label : str or None
        Label to display under the colorbar.  Ignored unless colorbar is True.
    basemap : Basemap object or None
        Use the specified basemap or create a default basemap using
        :func:`init_sky` when None.

    Returns
    -------
    basemap
        The basemap used for the plot, which will match the input basemap
        provided, or be a newly created basemap if None was provided.
    """
    import matplotlib.pyplot as plt

    data = np.asanyarray(data)
    if len(data.shape) != 2:
        raise ValueError('Expected 2D data array.')
    n_dec, n_ra = data.shape

    # Silently flatten, sort, and remove duplicates from the edges arrays.
    ra_edges = np.unique(ra_edges)
    dec_edges = np.unique(dec_edges)
    if len(ra_edges) != n_ra + 1:
        raise ValueError('Invalid ra_edges.')
    if len(dec_edges) != n_dec + 1:
        raise ValueError('Invalid dec_edges.')

    if ra_edges[0] != ra_edges[-1] - 360:
        raise ValueError('Invalid ra_edges, do not span 360 degrees.')

    clipped = prepare_data(data, mask, clip_lo, clip_hi)

    if basemap is None:
        basemap = init_sky()

    if basemap.lonmin + 360 != basemap.lonmax:
        raise RuntimeError('Can only handle all-sky projections for now.')

    # Shift RA gridlines so they overlap the map's left-edge RA.
    while ra_edges[0] > basemap.lonmin:
        ra_edges -= 360
    while ra_edges[0] <= basemap.lonmin - 360:
        ra_edges += 360

    # Find the first RA gridline that fits within the map's left edge.
    first = np.where(ra_edges >= basemap.lonmin)[0][0]

    if first > 0:
        # Wrap the data beyond the left edge around to the right edge.
        if ra_edges[first] > basemap.lonmin:
            # Split a wrap-around column into separate left and right columns.
            ra_edges = np.hstack(([basemap.lonmin], ra_edges[first:],
                                  ra_edges[:first] + 360, [basemap.lonmax]))
            clipped = np.hstack(
                (clipped[:, first:first + 1], clipped[:, first:],
                 clipped[:, :first], clipped[:, first:first + 1]))
        else:
            ra_edges = np.hstack((ra_edges[first:], ra_edges[:first + 1] + 360))
            clipped = np.hstack((clipped[:, first:], clipped[:, :first + 1]))

    # Build a 2D array of grid line intersections.
    grid_ra, grid_dec = np.meshgrid(ra_edges, dec_edges)

    mesh = basemap.pcolormesh(
        grid_ra, grid_dec, clipped, cmap=cmap, edgecolor='none',
        lw=0, latlon=True)

    if colorbar:
        bar = plt.colorbar(
            mesh, orientation='horizontal',
            spacing='proportional', pad=0.01, aspect=50)
        if label:
            bar.set_label(label)

    return basemap


def plot_sky(ra, dec, data=None, pix_shape='circle', nside=16, label='',
             projection='eck4', cmap='viridis', galactic_plane_color='black',
             discrete_colors=True, center_longitude=60, radius=2., epsi=0.2,
             alpha_tile=0.5, min_color=1, max_color=5, nsteps=5):
    """
    Routine that reads ra and dec (in degrees) and makes an all-sky plot
    of the data.

    Requires that matplotlib and basemap are installed. Also requires healpy
    when pix_shape is 'healpix'.

    Parameters
    ----------
    ra : array of :class: `float`
        Right ascension in degrees.
    dec : array of :class: `float`
        Declination in degrees.
    data : array of :class: `float or int`
        Weights to use (for example the tile-pass or values of E(B-V)).
    pix_shape : :class: `string`
        Shape of the pixels on the plot. It can take the values 'circle',
        'healpix', or 'square'.
    nside : :class: `int`
        It controls the number of pixels with healpix and square pixels.
        For healpix the celestial sphere is divided into 12*nside**2 pixels,
        and into 16*nside**2 for square pixels.
    label : :class: `string`, optional
        label for the colorbar.
    projection : :class: `string`, optional
        See :func:`init_sky`.
    cmap : :class: `string`, optional
        name of the matplotlib colormap to use. Default 'jet'.
    galactic_plane : :class: `bool`, optional
        See :func:`init_sky`.
    discrete_colors : :class: `bool`, optional
        if True it uses the data to create a linear discrete color-scale.
    center_longitude : :class: `float`, optional
        See :func:`init_sky`.
    radius : :class: `float`, optional
        Opening-angle radius in degrees to use when pix_shape is `circle`.
        Default 2.
    epsi : :class: `float`, optional
        it prevents ellipses to wrap around the edges. Only ellipses with
        abs(ra-180-center_longitude)>radius+epsi are plotted. If you want to
        plot all the ellipses set epsi to -radius (ellipses will wrap around
        the edges). Units are degrees. Default 0.2
    alpha_tile : :class: `float`, optional
        Transparency for the ellipses. 1 Opaque, 0 transparent. Default 0.5.
    min_color : :class: `float`, optional
        minimum value of the color scale if discrete_colors=True. Default 1
    max_color : :class: `float`, optional
        maximum value of the color scale if discrete_colors=True. Default 5
    nsteps : :class: `int`, optional
        number of intervals on the color scale if
        discrete_colors=True. Default 5

    Returns
    -------
    :class:`mpl_toolkits.basemap.Basemap`
       The Basemap object created for this plot, which can be used for
       additional projection and plotting operations.
    """
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    from matplotlib.collections import PolyCollection

    # Initialize the basemap to use.
    m = init_sky(projection, center_longitude, galactic_plane_color)

    if pix_shape not in ['circle','healpix','square']:
        raise KeyError(
            '%s shape invalid, try circle, healpix or square'%pix_shape)
    if discrete_colors:
        if data is None:
            raise ValueError('Error discrete_colors expects data!=None')
        else:
            # define the colormap
            cmap = plt.get_cmap(cmap)
            cmaplist = [cmap(i) for i in range(cmap.N)]
            cmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)
            # define the bins and normalize
            bounds = np.linspace(min_color,max_color,nsteps)
            norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    else:
        cmap = plt.get_cmap(cmap)
        norm = None

    if pix_shape=='healpix':
        import healpy as hp
        # get pixel area in degrees
        pixel_area = hp.pixelfunc.nside2pixarea(nside, degrees=True)
        #avoid pixels which may cause polygons to wrap around workaround
        drawing_mask = np.logical_and(
            np.fabs(ra-180-center_longitude)>2*np.sqrt(pixel_area)+epsi,
            np.fabs(ra+180-center_longitude)>2*np.sqrt(pixel_area)+epsi)
        ra=ra[drawing_mask]
        dec=dec[drawing_mask]
        if data!=None:
            data=data[drawing_mask]
        # find healpixels associated with input vectors
        pixels = hp.ang2pix(nside, 0.5*np.pi-np.radians(dec), np.radians(ra))
        # find unique pixels
        unique_pixels = np.unique(pixels)
        # count number of points in each pixel
        bincounts = np.bincount(pixels)
        # if no data provided, show counts per sq degree
        # otherwise, show mean per pixel
        if data is None:
            values = bincounts[unique_pixels]/pixel_area
        else:
            weighted_counts = np.bincount(pixels, weights=data)
            values = weighted_counts[unique_pixels]/bincounts[unique_pixels]
        # find pixel boundaries
        corners = hp.boundaries(nside, unique_pixels, step=1)
        corner_theta, corner_phi = hp.vec2ang(corners.transpose(0,2,1))
        corner_ra, corner_dec = (
            np.degrees(corner_phi), np.degrees(np.pi/2-corner_theta))
        # convert sky coords to map coords
        x,y = m(corner_ra, corner_dec)
        # regroup into pixel corners
        verts = np.array([x.reshape(-1,4), y.reshape(-1,4)]).transpose(1,2,0)
        # Make the collection and add it to the plot.
        coll = PolyCollection(
            verts, array=values, cmap=cmap, norm=norm, edgecolors='none')
        plt.gca().add_collection(coll)
        plt.gca().autoscale_view()
        # Add a colorbar for the PolyCollection
        plt.colorbar(
            coll, orientation='horizontal', cmap=cmap, norm=norm,
            spacing='proportional', pad=0.01, aspect=40, label=label)

    elif pix_shape=='square':
        nx, ny = 4*nside, 4*nside

        ra_bins = np.linspace(-180+center_longitude, 180+center_longitude, nx+1)
        cth_bins = np.linspace(-1., 1., ny+1)
        ra[ra>180+center_longitude]=ra[ra>180+center_longitude]-360
        if data==None:
            weights=np.ones(len(ra))
        else:
            weights=data
        density, _, _ = np.histogram2d(
            ra, np.sin(dec*np.pi/180.), [ra_bins, cth_bins], weights=weights)
        ra_bins_2d, cth_bins_2d = np.meshgrid(ra_bins, cth_bins)
        xs, ys = m(ra_bins_2d, np.arcsin(cth_bins_2d)*180/np.pi)
        new_density = np.ma.masked_where(density==0,density).T
        pcm = plt.pcolormesh(xs, ys, new_density,cmap=cmap, norm=norm)
        plt.colorbar(pcm,orientation='horizontal',cmap=cmap, norm=norm,
                     spacing='proportional', pad=0.04, label=label)

    elif pix_shape=='circle':
        if data==None:
            weights=np.ones(len(ra))
        else:
            weights=data
        ax = plt.gca()
        cmm = cm.ScalarMappable(norm=norm, cmap=cmap)
        color_array = cmm.to_rgba(weights)
        # Set the number of vertices for approximating the ellipse based
        # on the sky opening angle.
        n_pt = max(8, np.ceil(2 * radius))
        for i in range(0,len(ra)):
            if(np.fabs(ra[i]-180-center_longitude)>radius+epsi and
               np.fabs(ra[i]+180-center_longitude)>radius+epsi):
                poly = m.ellipse(
                    ra[i], dec[i], radius, radius, n_pt,
                    facecolor=color_array[i], zorder=10,alpha=alpha_tile)
        plt.colorbar(plt.imshow(
            np.array([(1,2),(3,4),(0,6)]),cmap=cmap, norm=norm),
            orientation='horizontal',cmap=cmap, norm=norm,
            spacing='proportional', pad=0.04, label=label)

    return m
