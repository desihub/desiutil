#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import, print_function
import glob
import os
import re
from subprocess import Popen, PIPE
# import ez_setup
# ez_setup.use_setuptools()
from setuptools import setup, Command, find_packages
from distutils.log import INFO
#
# Begin function/class definitions.
#
def update_version_py(productname,tag=None,debug=False):
    """Update the _version.py file.

    Args:
        productname (str) : The name of the package.
        tag (str, optional) : Set the version to this string, unconditionally.
        debug (bool, optional) : Print extra debug information.

    Returns:
        None
    """
    if tag is not None:
        ver = tag
    else:
        if not os.path.isdir(".git"):
            print("This is not a git repository.")
            return
        no_git = "Unable to run git, leaving py/{0}/_version.py alone.".format(productname)
        try:
            p = Popen(["git", "describe", "--tags", "--dirty", "--always"], stdout=PIPE, stderr=PIPE)
        except EnvironmentError:
            print("Could not run 'git describe'!")
            print(no_git)
            return
        out, err = p.communicate()
        if p.returncode != 0:
            print("Returncode = {0}".format(p.returncode))
            print(no_git)
            return
        ver = out.rstrip().split('-')[0]+'.dev'
        try:
            p = Popen(["git", "rev-list", "--count", "HEAD"], stdout=PIPE, stderr=PIPE)
        except EnvironmentError:
            print("Could not run 'git rev-list'!")
            print(no_git)
            return
        out, err = p.communicate()
        if p.returncode != 0:
            print("Returncode = {0}".format(p.returncode))
            print(no_git)
            return
        ver += out.rstrip()
    version_file = os.path.join('py',productname,'_version.py')
    with open(version_file, "w") as f:
        f.write( "__version__ = '{}'\n".format( ver ) )
    if debug:
        print("Set {0} to {1}".format( version_file, ver ))
    return
#
#
#
def get_version(productname,debug=False):
    """Get the value of ``__version__`` without having to import the module.

    Args:
        productname (str) : The name of the package.
        debug (bool, optional) : Print extra debug information.

    Returns:
        get_version (str) : The value of ``__version__``.
    """
    version_file = os.path.join('py',productname,'_version.py')
    if not os.path.isfile(version_file):
        if debug:
            print('Creating initial version file.')
        update_version_py(productname,debug=debug)
    ver = 'unknown'
    with open(version_file, "r") as f:
        for line in f.readlines():
            mo = re.match("__version__ = '(.*)'", line)
            if mo:
                ver = mo.group(1)
    return ver
#
#
#
class Version(Command):
    description = "update _version.py from git repo"
    user_options = [ ('tag=', 't', 'Set the version to a name in preparation for tagging.'), ]
    boolean_options = []
    def initialize_options(self):
        self.tag = None
    def finalize_options(self):
        pass
    def run(self):
        update_version_py(tag=self.tag)
        ver = get_version()
        self.announce("Version is now {}.".format( ver ), level=INFO)
#
# End of function/class definitions.
#
setup_keywords = dict()
#
# THESE SETTINGS NEED TO BE CHANGED FOR EVERY PRODUCT.
#
setup_keywords['name'] = 'desiutil'
setup_keywords['description'] = 'DESI utilities package'
setup_keywords['author'] = 'DESI Collaboration'
setup_keywords['author_email'] = 'desi-data@desi.lbl.gov'
setup_keywords['license'] = 'BSD'
setup_keywords['url'] = 'https://github.com/desihub/desiutil'
#
# END OF SETTINGS THAT NEED TO BE CHANGED.
#
setup_keywords['version'] = get_version(setup_keywords['name'])
#
# Use README.rst as long_description.
#
setup_keywords['long_description'] = ''
if os.path.exists('README.rst'):
    with open('README.rst') as readme:
        setup_keywords['long_description'] = readme.read()
#
# Set other keywords for the setup function.  These are automated, & should
# be left alone unless you are an expert.
#
# Treat everything in bin/ except *.rst as a script to be installed.
#
if os.path.isdir('bin'):
    setup_keywords['scripts'] = [fname for fname in glob.glob(os.path.join('bin', '*'))
        if not os.path.basename(fname).endswith('.rst')]
setup_keywords['provides'] = [setup_keywords['name']]
setup_keywords['requires'] = ['Python (>2.7.0)']
# setup_keywords['install_requires'] = ['Python (>2.7.0)']
setup_keywords['zip_safe'] = False
setup_keywords['use_2to3'] = True
setup_keywords['packages'] = find_packages('py')
setup_keywords['package_dir'] = {'':'py'}
setup_keywords['cmdclass'] = {'version': Version},
setup_keywords['test_suite']='{name}.test.{name}_test_suite.{name}_test_suite'.format(**setup_keywords)
#
# Autogenerate command-line scripts.
#
# setup_keywords['entry_points'] = {'console_scripts':['desiInstall = desiutil.install.main:main']}
#
# Run setup command.
#
setup(**setup_keywords)
