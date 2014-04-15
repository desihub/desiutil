# License information goes here
# -*- coding: utf-8 -*-
"""Install DESI software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def main():
    """Main program.

    Parameters
    ----------
    None

    Returns
    -------
    main : int
        Exit status that will be passed to ``sys.exit()``.
    """
    from sys import argv, executable, path
    from shutil import rmtree
    from os import environ, getenv, makedirs
    from os.path import basename, exists, isdir, join
    from argparse import ArgumentParser
    from .. import version
    from . import dependencies
    import subprocess
    #
    # Parse arguments
    #
    xct = basename(argv[0])
    parser = ArgumentParser(description=__doc__,prog=xct)
    parser.add_argument('-b', '--bootstrap', action='store_true', dest='bootstrap',
        help="Run in bootstrap mode to install the desiUtil product.")
    parser.add_argument('-d', '--default', action='store_true', dest='default',
        help='Make this version the default version.')
    parser.add_argument('-F', '--force', action='store_true', dest='force',
        help='Overwrite any existing installation of this product/version.')
    parser.add_argument('-m', '--module-home', action='store', dest='moduleshome',
        metavar='DIR',help='Set or override the value of $MODULESHOME',
        default=getenv('MODULESHOME'))
    parser.add_argument('-M', '--module-dir', action='store', dest='moduledir',
        metavar='DIR',help="Install module files in DIR.",default='')
    parser.add_argument('-r', '--root', action='store', dest='root',
        metavar='DIR', help='Set or override the value of $DESI_PRODUCT_ROOT',
        default=getenv('DESI_PRODUCT_ROOT'))
    parser.add_argument('-t', '--test', action='store_true', dest='test',
        help='Test mode.  Do not actually install anything.')
    parser.add_argument('-u', '--url', action='store',dest='url',
        metavar='URL',help="Download software from URL.",
        default='https://desi.lbl.gov/svn/code')
    parser.add_argument('-U', '--username', action='store', dest='username',
        metavar='USER',help="Set svn username to USER.",default=getenv('USER'))
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
        help='Print extra information.')
    parser.add_argument('-V', '--version', action='store_true', dest='version',
        help='Print version information.')
    parser.add_argument('product',nargs='?',default='NO PACKAGE',
        help='Name of product to install.')
    parser.add_argument('product_version',nargs='?',default='NO VERSION',
        help='Version of product to install.')
    options = parser.parse_args()
    debug = options.test or options.verbose
    #
    # Print version if requested.
    #
    if options.version:
        vers = version()
        print(vers)
        return 0
    #
    # Set up Modules
    #
    if options.moduleshome is None or not isdir(options.moduleshome):
        print("You do not appear to have Modules set up.")
        return 1
    initpy = join(options.moduleshome,'init','python.py')
    execfile(initpy,globals())
    #
    # Determine the product and version names.
    #
    baseproduct = basename(options.product)
    baseversion = basename(options.product_version)
    is_branch = options.product_version.startswith('branches')
    is_trunk = options.product_version == 'trunk'
    if is_trunk or is_branch:
        product_url = join(options.url,options.product,options.product_version)
    else:
        product_url = join(options.url,options.product,'tags',options.product_version)
    #
    # Check for existence of the URL.
    #
    command = ['svn','--username',options.username,'ls',product_url]
    if options.verbose:
        print(' '.join(command))
    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if options.verbose:
        print(out)
    if len(err) > 0:
        print("svn error while testing product URL:")
        print(err)
        return 1
    #
    # Figure out dependencies.  Use a dependency configuration file for this.
    # If two or more config files contain the same section & the same
    # keyword within that section, which one takes precedence?
    #
    deps = dependencies(baseproduct)
    for d in deps:
        if options.verbose:
            print("module('load','{0}')".format(d))
        module('load',d)
    #
    # Get the code
    #
    if is_trunk or is_branch:
        get_svn = 'co'
    else:
        get_svn = 'export'
    product_dir = "{0}_DIR".format(baseproduct.upper())
    working_dir = '{0}-{1}'.format(baseproduct,baseversion)
    command = ['svn','--username',options.username,get_svn,product_url,working_dir]
    if options.verbose:
        print(' '.join(command))
    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if options.verbose:
        print(out)
    if len(err) > 0:
        print("svn error while testing product URL:")
        print(err)
        return 1
    #if isdir(working_dir):
    #    os.environ[product_dir] = './'+working_dir
    #
    # Pick an install directory
    #
    nersc = None
    try:
        nersc = environ['NERSC_HOST']
    except KeyError:
        pass
    if options.root is None or not isdir(options.root):
        if nersc is not None:
            options.root = join('/project/projectdirs/desi/software',nersc)
        else:
            print("DESI_PRODUCT_ROOT is missing or not set.")
            return 1
    install_dir = join(options.root,baseproduct,baseversion)
    makedirs(install_dir)
    #
    # Prepare to configure module.
    #
    module_keywords = dict()
    module_keywords['name'] = baseproduct
    module_keywords['version'] = baseversion
    module_keywords['needs_bin'] = '# '
    module_keywords['needs_python'] = '# '
    module_keywords['needs_ld_lib'] = '# '
    scripts = [fname for fname in glob.glob(join(working_dir,'bin', '*'))
        if not basename(fname).endswith('.rst')]
    if len(scripts) > 0:
        module_keywords['needs_bin'] = ''
    if isdir(join(working_dir,'py')) or exists(join(working_dir,'setup.py')):
        module_keywords['needs_python'] = ''
        lib_dir = join(install_dir,'lib',module_keywords['pyversion'],'site-packages')
        #
        # If this is a python package, we need to manipulate the PYTHONPATH and
        # include the install directory
        #
        # If os.makedirs raises an exception, we want this to halt!
        makedirs(lib_dir)
        environ['PYTHONPATH'] = lib_dir + ':' + os.environ['PYTHONPATH']
        path.insert(int(path[0] == ''),lib_dir)
    #
    # Get the Python version
    #
    module_keywords['pyversion'] = "python{0:d}.{1:d}".format(*sys.version_info)
    #
    # Run the install
    #
    command = [executable, 'setup.py', 'install', '--prefix={0}'.format(install_dir)]
    if options.verbose:
        print(' '.join(command))
    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if options.verbose:
        print(out)
    if len(err) > 0:
        print("Error during installation:")
        print(err)
        return 1
    #
    # Process the module file.
    #
    module_file = join(working_dir,'etc',baseproduct+'.module')
    if exists(module_file):
        if not isdir(join(options.moduledir,baseproduct)):
            makedirs(join(options.moduledir,baseproduct))
        install_module_file = join(options.moduledir,baseproduct,baseversion)
        with open(module_file) as m:
            mod = m.read().format(**module_keywords)
        with open(install_module_file,'w') as m:
            m.write(mod)
        if options.default:
            dot_version = '''#%Module1.0
set ModulesVersion "{0}"
'''.format(baseversion)
            install_version_file = join(options.moduledir,baseproduct,'.version')
            with open(install_version_file,'w') as v:
                v.write(dot_version)
    #
    # Clean up
    #
    rmtree(working_dir)
    return 0
#
#
#
if __name__ == '__main__':
    from sys import exit
    exit(main())
