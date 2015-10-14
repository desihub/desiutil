# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Easy updates of package version.
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
from setuptools import Command
from . import update_version, get_version
from distutils.log import INFO
#
class DesiVersion(Command):
    """Allow users to easily update the package version with ``python setup.py version``.
    """
    description = "update _version.py from git repo"
    user_options = [ ('tag=', 't', 'Set the version to a name in preparation for tagging.'), ]
    boolean_options = []
    def initialize_options(self):
        self.tag = None
    def finalize_options(self):
        pass
    def run(self):
        meta = self.distribution.metadata
        update_version(meta.get_name(),tag=self.tag)
        ver = get_version(meta.get_name())
        self.announce("Version is now {}.".format( ver ), level=INFO)
