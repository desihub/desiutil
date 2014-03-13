#!/usr/bin/env python
# License information goes here
#
# This setup.py file is designed to be invoked with --prefix explicitly set.
# For example
#
#   python setup.py install --prefix /project/projectdirs/desi/software
#
# Imports
#
import glob
import os
import sys
import warnings
from setuptools import setup, find_packages
#
# Import this module to get __doc__ and version().
#
setup_keywords = dict()
sys.path.insert(int(sys.path[0] == ''),'./py')
try:
    import desiUtil
    setup_keywords['long_description'] = desiUtil.__doc__
    setup_keywords['version'] = desiUtil.version()
except ImportError:
    #
    # Try to get the long description from the README.rst file.
    #
    if os.path.exists('README.rst'):
        with open('README.rst') as readme:
            setup_keywords['long_description'] = readme.read()
    else:
        setup_keywords['long_description'] = ''
    setup_keywords['version'] = '0.0.1.dev'
#
# Obtain svn information.
#
def get_svn_devstr():
    """Get the svn revision number.

    Parameters
    ----------
    None

    Returns
    -------
    get_svn_devstr : str
        The latest svn revision number.
    """
    from subprocess import Popen, PIPE
    proc = Popen(['svnversion','-n'],stdout=PIPE,stderr=PIPE)
    out, err = proc.communicate()
    rev = out
    if ':' in out:
        rev = out.split(':')[1]
    rev = rev.replace('M','').replace('S','').replace('P','')
    return rev
#
# Indicates if this version is a release version.
#
RELEASE = 'dev' not in setup_keywords['version']
if not RELEASE:
    setup_keywords['version'] += get_svn_devstr()
#
# Set general settings.  Change these as needed.
#
setup_keywords['name'] = 'desiUtil'
setup_keywords['description'] = 'DESI utilities package'
setup_keywords['author'] = 'Benjamin Alan Weaver'
setup_keywords['author_email'] = 'baweaver@lbl.gov'
setup_keywords['license'] = 'BSD'
setup_keywords['url'] = 'https://desi.lbl.gov/svn/code/tools/desiUtil'
#
# Set other keywords for the setup function.  These are automated, & should
# be left alone unless you are an expert.
#
# Treat everything in bin/ except *.rst as a script to be installed.
#
setup_keywords['_needs_bin'] = '# '
setup_keywords['_needs_python'] = '' # Since this is a Python package this will always be needed.
setup_keywords['_needs_ld_lib'] = '# '
setup_keywords['scripts'] = [fname for fname in glob.glob(os.path.join('bin', '*'))
    if not os.path.basename(fname).endswith('.rst')]
if len(setup_keywords['scripts']) > 0:
    setup_keywords['_needs_bin'] = ''
setup_keywords['provides'] = ['desiUtil']
setup_keywords['requires'] = ['Python (>2.6.0)']
#setup_keywords['install_requires'] = ['Python (>2.6.0)']
setup_keywords['zip_safe'] = False
setup_keywords['use_2to3'] = True
setup_keywords['packages'] = find_packages('py')
setup_keywords['package_dir'] = {'':'py'}
#
# If we are using --prefix, manipulate the prefix directory and make sure
# it is in sys.path
#
prefix = [arg for arg in sys.argv if arg.startswith('--prefix')]
if len(prefix) > 0 and 'install' in sys.argv:
    i = sys.argv.index(prefix[0])
    prefdir = prefix[0].split('=')[1]
    nersc_host = os.getenv('NERSC_HOST')
    if nersc_host is not None:
        if os.path.basename(prefdir) != nersc_host:
            prefdir = os.path.join(prefdir,nersc_host)
    if os.path.basename(prefdir) == setup_keywords['name']:
        prefdir = os.path.join(prefdir,setup_keywords['version'])
    else:
        prefdir = os.path.join(prefdir,setup_keywords['name'],setup_keywords['version'])
    sys.argv[i] = '--prefix='+prefdir
    # print(sys.argv)
    #
    # Get the Python version
    #
    setup_keywords['_pyversion'] = "python{0:d}.{1:d}".format(*sys.version_info)
    libdir = os.path.join(prefdir,'lib',setup_keywords['_pyversion'],'site-packages')
    # If os.makedirs raises an exception, we want this to halt!
    os.makedirs(libdir)
    os.environ['PYTHONPATH'] = libdir + ':' + os.environ['PYTHONPATH']
    sys.path.insert(int(sys.path[0] == ''),libdir)
    #
    # Process the module file.
    #
    module_file = os.path.join('.','etc',setup_keywords['name']+'.module')
    if os.path.exists(module_file):
        with open(module_file) as m:
            mod = m.read().format(**setup_keywords)
        new_module_file = os.path.join('.','etc',setup_keywords['name']+'_'+setup_keywords['version']+'.module')
        with open(new_module_file,'w') as m:
            m.write(mod)
else:
    if 'install' in sys.argv:
        print("Warning, you are attempting to install without setting --prefix.  This is not recommended.")
        sys.exit(1)
#
# Run setup command.  setup() will emit warnings about unknown keywords we
# will be passing to it, so we suppress them.
#
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    setup(**setup_keywords)
