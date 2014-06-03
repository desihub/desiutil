# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
"""
========
desiUtil
========

This package provides low-level utilities for general use by DESI_.

.. _DESI: http://desi.lbl.gov
"""
from .install import version
#
# Set version string.
#
__version__ = version($HeadURL$)
#
# Clean up namespace
#
del version
