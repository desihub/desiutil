# License information goes here
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
"""
================
desiUtil.install
================

This package contains code for installing DESI software products.
"""

from .dependencies import dependencies
from .get_svn_devstr import get_svn_devstr
from .most_recent_tag import most_recent_tag
from .version import version
