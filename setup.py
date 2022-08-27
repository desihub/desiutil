#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
# Standard imports
#
import glob
import os
import sys
#
# setuptools' sdist command ignores MANIFEST.in
#
from distutils.command.sdist import sdist as DistutilsSdist
from setuptools import setup, find_packages
#
# desiutil needs to import some of its own code.
#
sys.path.insert(int(sys.path[0] == ''), os.path.abspath('./py'))
import desiutil.setup as ds
#
# Begin setup
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
setup_keywords['version'] = ds.get_version(setup_keywords['name'])
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
setup_keywords['python_requires'] = '>=3.5'
setup_keywords['zip_safe'] = False
setup_keywords['use_2to3'] = False
setup_keywords['packages'] = find_packages('py')
setup_keywords['package_dir'] = {'': 'py'}
setup_keywords['cmdclass'] = {'version': ds.DesiVersion,
                              'test': ds.DesiTest,
                              'api': ds.DesiAPI,
                              'sdist': DistutilsSdist}
setup_keywords['test_suite']='{name}.test.{name}_test_suite'.format(**setup_keywords)
#
# Autogenerate command-line scripts.
#
# setup_keywords['entry_points'] = {'console_scripts':['desiInstall = desiutil.install:main',
#                                                      'desi_data_census = desiutil.census:main',
#                                                      'desi_module_file = desiutil.modules:main']}
#
# Add internal data directories.
#
setup_keywords['package_data'] = {'desiutil': ['data/*'],
                                  'desiutil.test': ['t/*']}
#
# Run setup command.
#
setup(**setup_keywords)
