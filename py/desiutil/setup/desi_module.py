# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Install Module files.
"""
#
from __future__ import absolute_import, division, print_function
from setuptools import Command
from distutils.log import INFO
# from .get_version import get_version
# from .update_version import update_version
#
class DesiModule(Command):
    """Allow users to install module files with ``python setup.py module_file``.
    """
    description = "install a module file for this package"
    # user_options = [ ('tag=', 't', 'Set the version to a name in preparation for tagging.'), ]
    user_options = []
    boolean_options = []
    def initialize_options(self):
        # self.tag = None
        pass
    def finalize_options(self):
        pass
    def run(self):
        meta = self.distribution.metadata
        # update_version(meta.get_name(),tag=self.tag)
        # ver = get_version(meta.get_name())
        # self.announce("Version is now {}.".format( ver ), level=INFO)
