# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""
================
desiutil.install
================

This package contains code for installing DESI software products.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
from .desi_install import DesiInstall
from .dependencies import dependencies
from .get_svn_devstr import get_svn_devstr
from .git_version import git_version
from .known_products import known_products
from .most_recent_git_tag import most_recent_git_tag
from .most_recent_svn_tag import most_recent_svn_tag
from .svn_version import svn_version
