# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.sklearn.
"""
from __future__ import absolute_import, print_function
import unittest
from tempfile import NamedTemporaryFile
from pkg_resources import resource_filename
import numpy as np
from astropy.io import fits
from ..sklearn import GaussianMixtureModel as GMM


class TestSKLearn(unittest.TestCase):
    """Test desiutil.sklearn
    """

    @classmethod
    def setUpClass(cls):
        cls.data = resource_filename('desiutil.test', 't/qso_gmm.fits')
        cls.weights = np.array([0.09399423, 0.02817785, 0.16842868,
                                0.25130015, 0.18764636, 0.22785686,
                                0.01427254, 0.02832333])
        cls.means = np.array([[21.8674558, 21.65599582, 21.35046531,
                               20.56470438, 20.63950263, 19.53187692,
                               16.23383613],
                              [19.87466797, 19.43940682, 19.10314704,
                               18.22932306, 17.79830893, 16.17580678,
                               14.42860774],
                              [22.39168723, 22.01403421, 21.53127858,
                               20.5213737, 19.99556088, 18.60553745,
                               16.24232095],
                              [21.45390669, 21.02017782, 20.57682578,
                               19.43739724, 19.01619359, 17.61300064,
                               15.84915674],
                              [21.09669942, 20.84510702, 20.57755684,
                               19.66137068, 19.22199292, 18.33010152,
                               17.32762037],
                              [19.96967104, 19.7419634, 19.57586161,
                               18.73100918, 18.18709966, 16.94859119,
                               15.73005131],
                              [18.29425202, 17.18655695, 17.16808001,
                               16.61722985, 16.88517014, 16.83822062,
                               15.54243996],
                              [23.94602113, 21.60288145, 21.97758493,
                               20.88288992, 20.56319688, 18.29005688,
                               16.12080985]])

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load(self):
        """Test loading a model from a file.
        """
        model = GMM.load(self.data)
        self.assertEqual(model.covtype, 'full')
        self.assertEqual((model.n_components, model.n_dimensions),
                         self.means.shape)
        self.assertTrue(np.allclose(model.weights, self.weights))
        self.assertTrue(np.allclose(model.means, self.means))

    def test_save(self):
        """Test saving a model from to file.
        """
        model = GMM(np.ones((5,), dtype=np.float64),
                    np.zeros((5, 3), dtype=np.float64),
                    np.zeros((5, 3, 3), dtype=np.float64),
                    'full')
        with NamedTemporaryFile(suffix='.fits') as f:
            model.save(model, f.name)
            with fits.open(f.name) as hdulist:
                self.assertEqual(len(hdulist), 3)
                self.assertEqual(hdulist[0].header['COVTYPE'], 'full')
                self.assertTrue(np.allclose(hdulist['WEIGHTS'].data,
                                            np.ones((5,), dtype=np.float64)))
                self.assertTrue(np.allclose(hdulist['MEANS'].data,
                                            np.zeros((5, 3),
                                                     dtype=np.float64)))

    def test_sample(self):
        """Test sampling from a model.
        """
        model = GMM(np.ones((5,), dtype=np.float64),
                    np.zeros((5, 3), dtype=np.float64),
                    np.zeros((5, 3, 3), dtype=np.float64),
                    'foo')
        with self.assertRaises(ValueError) as cm:
            model.sample()
        self.assertEqual(str(cm.exception),
                         'Covariance type "foo" is not yet implemented.')


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
