# License information goes here
# -*- coding: utf-8 -*-
"""
===============================
desiUtil.install.known_products
===============================

This module contains a dictionary that maps product names to their path
within the DESI svn repository.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
known_products = {
    'desiDataModel': 'archive/desiDataModel',
    'desimodel': 'desimodel',
    'plate_layout': 'focalplane/plate_layout',
    'positioner_control': 'focalplane/positioner_control',
    'bbspecsim': 'spectro/bbspecsim',
    'desispec': 'spectro/desispec',
    'dspecsim', 'spectro/dspecsim',
    'templates': 'spectro/templates',
    'fiberassignment': 'survey/fiberassignment',
    'surveyplan': 'survey/surveyplan',
    'elg_deep2': 'targeting/elg_deep2',
    'desiAdmin': 'tools/desiAdmin',
    'desiModules': 'tools/desiModules',
    'desiTemplate': 'tools/desiTemplate',
    'desiTree': 'tools/desiTree',
    'desiUtil': 'tools/desiUtil',
    }
