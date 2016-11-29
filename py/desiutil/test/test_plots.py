# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Test desiutil.plots.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
# The line above will help with 2to3 support.
import unittest
import shutil, tempfile
import os
import numpy as np
import sys
#Set non-interactive backend for Travis
import matplotlib
matplotlib.use('agg')

import matplotlib.pyplot as plt

try:
    basestring
except NameError:  # For Python 3
    basestring = str

class TestPlotSlices(unittest.TestCase):
    """Test desiutil.plots
    """

    @classmethod
    def setUpClass(self):
        self.test_dir = tempfile.mkdtemp()
        self.plot_file = os.path.join(self.test_dir,'test_slices.png')
   
    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.test_dir)       
 
    def test_slices(self):
        """Test plot_slices
        """
        # Random data
        from ..plots import plot_slices
        x = np.random.rand(1000)
        y = np.random.randn(1000)
        # Run 
        ax_slices = plot_slices(x,y,0.,1.,0.) 
        ax_slices.set_ylabel('N sigma')
        ax_slices.set_xlabel('x')
        fig = plt.gcf()
        fig.savefig(self.plot_file)
        print('Saved file')
class TestPlotSky(unittest.TestCase):    
    @classmethod
    def setUpClass(self):
        self.test_dir = tempfile.mkdtemp()
        self.plot_file = os.path.join(self.test_dir,'test_sky.png')
   
    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.test_dir)    

    def test_plot_sky(self):
        """Test plot_sky
        """ 
        from ..plots import plot_sky
        ra = 360.*np.random.rand(200)
        dec = 360.*np.random.rand(200)
        #Run
        ax = plot_sky(ra,dec,discrete_colors=False,pix_shape='square')
        plt.savefig(self.plot_file)

def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
