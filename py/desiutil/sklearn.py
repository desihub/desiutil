# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
================
desiutil.sklearn
================

Useful functions from the sklearn python package.
"""


class GaussianMixtureModel(object):
    """Read and sample from a pre-defined Gaussian mixture model.

    Parameters
    ----------
    weights : :class:`numpy.ndarray`
        A 1D array of weights.  The length of the array is the number of
        components
    means : :class:`numpy.ndarray`
        A 2D array of means.  The number of rows is the number of components.
        The number of columns is the number of dimensions.
    covars : :class:`numpy.ndarray`
        A 3D array of covariances.  The first dimension is the number of
        components.  Each component has a 2D array with size given by the
        number of dimensions.
    covtype : :class:`str`, optional
        Type of covariance.  Defaults to 'full'.
    """

    def __init__(self, weights, means, covars, covtype='full'):
        self.weights = weights
        self.means = means
        self.covars = covars
        self.covtype = covtype
        self.n_components, self.n_dimensions = self.means.shape

    @staticmethod
    def save(model, filename):
        """Save a model to a file.

        Parameters
        ----------
        model : :class:`desiutil.sklearn.GaussianMixtureModel`
            The model to be saved.
        filename : :class:`str`
            The name of the file to save to.
        """
        from astropy.io import fits
        hdus = fits.HDUList()
        hdr = fits.Header()
        try:
            hdr['covtype'] = model.covariance_type
            hdus.append(fits.ImageHDU(model.weights_, name='weights', header=hdr))
            hdus.append(fits.ImageHDU(model.means_, name='means'))
            hdus.append(fits.ImageHDU(model.covariances_, name='covars'))
        except AttributeError:
            hdr['covtype'] = model.covtype
            hdus.append(fits.ImageHDU(model.weights, name='weights', header=hdr))
            hdus.append(fits.ImageHDU(model.means, name='means'))
            hdus.append(fits.ImageHDU(model.covars, name='covars'))
        hdus.writeto(filename, overwrite=True)

    @staticmethod
    def load(filename):
        """Load a model from a file.

        Parameters
        ----------
        filename : :class:`str`
            The name of the file to load from.

        Returns
        -------
        :class:`desiutil.sklearn.GaussianMixtureModel`
            The model that was in `filename`.
        """
        from astropy.io import fits
        hdus = fits.open(filename, memmap=False)
        hdr = hdus[0].header
        covtype = hdr['covtype']
        model = GaussianMixtureModel(hdus['weights'].data, hdus['means'].data,
                                     hdus['covars'].data, covtype)
        hdus.close()
        return model

    def sample(self, n_samples=1, random_state=None):
        """Sample from a model.

        Parameters
        ----------
        n_samples : :class:`int`, optional
            Number of samples to return, default 1.
        random_state : :class:`numpy.random.RandomState`, optional
            A random state object.

        Returns
        -------
        :class:`numpy.ndarray`
            An array containing the samples.

        Raises
        ------
        ValueError
            If the covariance type is unknown.
        """
        import numpy as np

        if self.covtype != 'full':
            raise ValueError(('Covariance type "{0}" is not yet ' +
                              'implemented.').format(self.covtype))

        # Code adapted from sklearn's GMM.sample()
        if random_state is None:
            random_state = np.random.RandomState()

        weight_cdf = np.cumsum(self.weights)
        X = np.empty((n_samples, self.n_dimensions))
        rand = random_state.rand(n_samples)
        # decide which component to use for each sample
        comps = weight_cdf.searchsorted(rand)
        # for each component, generate all needed samples
        for comp in range(self.n_components):
            # occurrences of current component in X
            comp_in_X = (comp == comps)
            # number of those occurrences
            num_comp_in_X = comp_in_X.sum()
            if num_comp_in_X > 0:
                X[comp_in_X] = random_state.multivariate_normal(
                    self.means[comp], self.covars[comp], num_comp_in_X)
        return X
