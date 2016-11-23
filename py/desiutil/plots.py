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

def plot_sky(ra, dec, data=None, pix_shape='ellipse', nside=16, label='', projection='eck4', cmap='jet', hide_galactic_plane=False, discrete_colors=True, center_longitude=0, radius=2., epsi=0.2, alpha_tile=0.5, min_color=1, max_color=5, nsteps=5):
    """
    Routine that reads ra and dec with the proper units (requires astropy units) and makes an all-sky plot of the desired
    data.
    Requires Basemap installed and astropy.units
    
    Parameters
    ----------

        ra : array of :class: `astropy.angle`
             Right ascension with units.
        dec : array of :class: `astropy.angle`
             Declination with units.
        data : array of :class: `float or int`
             Weights to use (for example the tile-pass or values of E(B-V)).
        pix_shape : :class: `string`
             Desired shape of the pixels on the plot. It can take the values 'ellipse', 'healpix', and 'square'
             nside : int, it controls the number of pixels with healpix and square pixels. For healpix the whole celestial sphere is
             divided into 12*nside**2 pixels, for square pixels it is divided into 16*nside**2.
        label : :class: `string`, optional
             label for the colorbar.
        projection : :class: `string`, optional
             projection scheme used to show the map. 'eck4', 'kav7', and 'moll' recommended for full sky maps: Default 'eck4'.
        cmap : :class: `string`, optional
             name of the matplotlib colormap to use. Default 'jet'.
        hide_galactic_plane : :class: `bool`, optional
             if True it hides the galactic plane in the plot, if False it shows it. Default False.
        discrete_colors : :class: `bool`, optional
             if True it uses the data to create a linear discrete color-scale.
        center_longitude : :class: `float`, optional
             center longitude for the plot in degrees. Default 0.
        radius : :class: `float`, optional
             radius of the circle in degrees. Default 2.
        epsi : :class: `float`, optional
             it prevents ellipses to wrap around the edges. Only ellipses with |ra-180-center_longitude|>radius+epsi are plotted. If
             you want to plot all the ellipses set epsi to -radius (some ellipses may wrap around the edges). Default 0.2
        alpha_tile : :class: `float`, optional
             value between 0 and 1 of transparency for the ellipses. 1 Opaque, 0 transparent.
        min_color : :class: `float`, optional
             minimum value of the color scale if discrete_colors=True. Default 1
        max_color : :class: `float`, optional
             maximum value of the color scale if discrete_colors=True. Default 5
        nsteps : :class: `int`, optional
             number of intervals on the color scale if discrete_colors=True. Default 5

    Returns
    -------
    :class:`matplotlib.axes.Axes` 
        The Axes object for the plot. It creates a figure if there was no previous figure and if data is not provided it returns counts per square-degree if healpix
            or square pixels are created. If you choose the option ellipse it plots as many ellipses as ra,dec points provided (it may be slow).
    """
    from matplotlib.collections import PolyCollection
    from astropy.coordinates import SkyCoord
    import matplotlib.pyplot as plt
    import astropy.units as u
    import matplotlib.cm as cm
    import numpy as np
    from matplotlib.patches import Polygon
    from mpl_toolkits.basemap import pyproj
    from mpl_toolkits.basemap import Basemap
    import matplotlib
    #---------
    # Add ellipses to Basemap
    #--------

    class Basemap(Basemap):
        #Code from http://stackoverflow.com/questions/8161144/drawing-ellipses-on-matplotlib-basemap-projections
        #It adds ellipses to the class Basemap to use in plotsky. This is only used in plotsky and includes the basemap
        #dependencies.
     def ellipse(self, x0, y0, a, b, n, ax=None, **kwargs):
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
      
    ra=ra.to(u.deg).value
    dec=dec.to(u.deg).value
    if pix_shape not in ['ellipse','healpix','square']:
        print('Pixel shape invalid, try ellipse, healpix or square')
    if discrete_colors:
        if(data is None):
            print('Error discrete_colors expects data!=None')
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
    if(pix_shape=='healpix'):
        import healpy as hp
        # get pixel area in degrees
        pixel_area = hp.pixelfunc.nside2pixarea(nside, degrees=True)
        #avoid pixels which may cause polygons to wrap around workaround
        drawing_mask = np.logical_and(np.fabs(ra-180-center_longitude)>2*np.sqrt(pixel_area)+epsi,np.fabs(ra+180-center_longitude)>2*np.sqrt(pixel_area)+epsi)
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
        corner_ra, corner_dec = np.degrees(corner_phi), np.degrees(np.pi/2-corner_theta)
        # set up basemap
        m = Basemap(projection=projection, lon_0=center_longitude, resolution='c', celestial=True)
        m.drawmeridians(np.arange(0, 360, 60), labels=[0,0,1,0], labelstyle='+/-')
        m.drawparallels(np.arange(-90, 90, 15), labels=[1,0,0,0], labelstyle='+/-')
        m.drawmapboundary()
        # convert sky coords to map coords 
        x,y = m(corner_ra, corner_dec)
        # regroup into pixel corners
        verts = np.array([x.reshape(-1,4), y.reshape(-1,4)]).transpose(1,2,0)
        # Make the collection and add it to the plot.
        coll = PolyCollection(verts, array=values, cmap=cmap, norm=norm, edgecolors='none')
        plt.gca().add_collection(coll)
        plt.gca().autoscale_view()
        if not hide_galactic_plane:
            # generate vector in galactic coordinates and convert to equatorial coordinates
            galactic_l = np.linspace(0, 2*np.pi, 1000)
            galactic_plane = SkyCoord(l=galactic_l*u.radian, b=np.zeros_like(galactic_l)*u.radian, frame='galactic').fk5
            # project to map coordinates
            galactic_x, galactic_y = m(galactic_plane.ra.degree, galactic_plane.dec.degree)
            m.scatter(galactic_x, galactic_y, marker='.', s=2, c='k')
        # Add a colorbar for the PolyCollection
        plt.colorbar(coll, orientation='horizontal',cmap=cmap, norm=norm, spacing='proportional', pad=0.01, aspect=40, label=label)
    if(pix_shape=='square'):
        nx, ny = 4*nside, 4*nside

        ra_bins = np.linspace(-180+center_longitude, 180+center_longitude, nx+1)
        cth_bins = np.linspace(-1., 1., ny+1)
        ra[ra>180+center_longitude]=ra[ra>180+center_longitude]-360
        if data==None:
            weights=np.ones(len(ra))
        else:
            weights=data
        density, _, _ = np.histogram2d(ra, np.sin(dec*np.pi/180.), [ra_bins, cth_bins], weights=weights)
        ra_bins_2d, cth_bins_2d = np.meshgrid(ra_bins, cth_bins)
        m = Basemap(projection=projection, lon_0=center_longitude, resolution='l', celestial=True)
        m.drawmeridians(np.arange(0, 360, 60), labels=[0,0,1,0], labelstyle='+/-')
        m.drawparallels(np.arange(-90, 90, 15), labels=[1,0,0,0], labelstyle='+/-')
        m.drawmapboundary()
        xs, ys = m(ra_bins_2d, np.arcsin(cth_bins_2d)*180/np.pi)
        new_density = np.ma.masked_where(density==0,density).T
        pcm = plt.pcolormesh(xs, ys, new_density,cmap=cmap, norm=norm)
        plt.colorbar(pcm,orientation='horizontal',cmap=cmap, norm=norm, spacing='proportional', pad=0.04, label=label)
        if not hide_galactic_plane:
            # generate vector in galactic coordinates and convert to equatorial coordinates
            galactic_l = np.linspace(0, 2*np.pi, 1000)
            galactic_plane = SkyCoord(l=galactic_l*u.radian, b=np.zeros_like(galactic_l)*u.radian, frame='galactic').fk5
            # project to map coordinates
            galactic_x, galactic_y = m(galactic_plane.ra.degree, galactic_plane.dec.degree)
            m.scatter(galactic_x, galactic_y, marker='.', s=2, c='k')
    if(pix_shape=='ellipse'):
        m = Basemap(projection=projection, lon_0=center_longitude, resolution='l', celestial=True)
        m.drawmeridians(np.arange(0, 360, 60), labels=[0,0,1,0], labelstyle='+/-')
        m.drawparallels(np.arange(-90, 90, 15), labels=[1,0,0,0], labelstyle='+/-')
        m.drawmapboundary()
        if not hide_galactic_plane:
            # generate vector in galactic coordinates and convert to equatorial coordinates
            galactic_l = np.linspace(0, 2*np.pi, 1000)
            galactic_plane = SkyCoord(l=galactic_l*u.radian, b=np.zeros_like(galactic_l)*u.radian, frame='galactic').fk5
            # project to map coordinates
            galactic_x, galactic_y = m(galactic_plane.ra.degree, galactic_plane.dec.degree)
            m.scatter(galactic_x, galactic_y, marker='.', s=2, c='k')
        if data==None:
            weights=np.ones(len(ra))
        else:
            weights=data
        ax = plt.gca()
        cmm = cm.ScalarMappable(norm=norm, cmap=cmap)
        color_array = cmm.to_rgba(weights)
        for i in range(0,len(ra)):
            if(np.fabs(ra[i]-180-center_longitude)>radius+epsi and np.fabs(ra[i]+180-center_longitude)>radius+epsi):
                poly = m.ellipse(ra[i], dec[i], radius, radius, 8, facecolor=color_array[i], zorder=10,alpha=alpha_tile)
        plt.colorbar(plt.imshow(np.array([(1,2),(3,4),(0,6)]),cmap=cmap, norm=norm),orientation='horizontal',cmap=cmap, norm=norm, spacing='proportional', pad=0.04, label=label)
    axis = plt.gca()
    return axis
 
