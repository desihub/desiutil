# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
from __future__ import absolute_import
#
# Don't import this function.  It causes a scary-seeming warning of the form:
# .../lib/python3.5/runpy.py:125: RuntimeWarning:
#     'desiutil.test.desiutil_test_suite' found in sys.modules after
#     import of package 'desiutil.test', but prior to execution of
#     'desiutil.test.desiutil_test_suite'; this may result in unpredictable behaviour
#        warn(RuntimeWarning(msg))
#
# from .desiutil_test_suite import runtests
