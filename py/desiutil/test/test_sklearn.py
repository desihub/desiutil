# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.sklearn.
"""
from __future__ import absolute_import, print_function
import unittest
from ..sklearn import GaussianMixtureModel


class TestSKLearn(unittest.TestCase):
    """Test desispec.sklearn
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
