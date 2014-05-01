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
    import glob
    import logging
    import subprocess
    import datetime
    from sys import argv, executable, path, version_info
    from shutil import copyfile, copytree, rmtree
    from os import chdir, environ, getcwd, getenv, makedirs
    from os.path import abspath, basename, exists, isdir, join
    from argparse import ArgumentParser
    from .. import version
    from . import dependencies
    #
    # Parse arguments
    #
    xct = basename(argv[0])
    parser = ArgumentParser(description=__doc__,prog=xct)
    parser.add_argument('-b', '--bootstrap', action='store_true', dest='bootstrap',
        help="Run in bootstrap mode to install the desiUtil product.")
    parser.add_argument('-d', '--default', action='store_true', dest='default',
        help='Make this version the default version.')
    parser.add_argument('-D', '--documentation', action='store_true', dest='documentation',
        help='Build any Sphinx or Doxygen documentation.')
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
    logger = logging.getLogger('desiInstall')
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s Log - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    #
    # Print version if requested.
    #
    if options.version:
        vers = version()
        print(vers)
        return 0
    #
    # Sanity check options
    #
    if options.product == 'NO PACKAGE' or options.product_version == 'NO VERSION':
        if options.bootstrap:
            options.default = True
            options.product = 'tools/desiUtil'
            command = ['svn','--username',options.username,'ls',join(options.url,options.product,'tags')]
            logger.debug(' '.join(command))
            proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = proc.communicate()
            logger.debug(out)
            if len(err) > 0:
                logger.error("svn error while detecting desiUtil versions:")
                logger.error(err)
                return 1
            options.product_version = sorted([v.rstrip('/') for v in out.split('\n') if len(v) > 0])[-1]
            logger.info("Selected desiUtil/{0} for installation.".format(options.product_version))
        else:
            logger.error("You must specify a product and a version!")
            return 1
    #
    # Set up Modules
    #
    if options.moduleshome is None or not isdir(options.moduleshome):
        logger.error("You do not appear to have Modules set up.")
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
    logger.debug(' '.join(command))
    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = proc.communicate()
    logger.debug(out)
    if len(err) > 0:
        logger.error("svn error while testing product URL:")
        logger.error(err)
        return 1
    #
    # Figure out dependencies.  Use a dependency configuration file for this.
    # If two or more config files contain the same section & the same
    # keyword within that section, which one takes precedence?
    #
    deps = dependencies(baseproduct)
    for d in deps:
        logger.debug("module('load','{0}')".format(d))
        module('load',d)
    #
    # Get the code
    #
    if is_trunk or is_branch:
        get_svn = 'checkout'
    else:
        get_svn = 'export'
    product_dir = "{0}_DIR".format(baseproduct.upper())
    working_dir = join(abspath('.'),'{0}-{1}'.format(baseproduct,baseversion))
    if isdir(working_dir):
        logger.info("Detected old working directory, {0}. Deleting...".format(working_dir))
        rmtree(working_dir)
    command = ['svn','--username',options.username,get_svn,product_url,working_dir]
    logger.debug(' '.join(command))
    proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = proc.communicate()
    logger.debug(out)
    if len(err) > 0:
        logger.error("svn error while downloading product code:")
        logger.error(err)
        return 1
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
            logger.error("DESI_PRODUCT_ROOT is missing or not set.")
            return 1
    install_dir = join(options.root,baseproduct,baseversion)
    if isdir(install_dir) and not options.test:
        if options.force:
            rmtree(install_dir)
        else:
            logger.error("Install directory, {0}, already exists!".format(install_dir))
            return 1
    if not options.test:
        try:
            makedirs(install_dir)
        except OSError as ose:
            logger.error(ose.strerror)
            return 1
    #
    # Prepare to configure module.
    #
    module_keywords = dict()
    module_keywords['name'] = baseproduct
    module_keywords['version'] = baseversion
    module_keywords['dependencies'] = "\n".join(dependencies(baseproduct,modulefile=True))
    module_keywords['needs_bin'] = '# '
    module_keywords['needs_python'] = '# '
    module_keywords['needs_ld_lib'] = '# '
    module_keywords['pyversion'] = "python{0:d}.{1:d}".format(*version_info)
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
        if not options.test:
            try:
                makedirs(lib_dir)
            except OSError as ose:
                logger.error(ose.strerror)
                return 1
            environ['PYTHONPATH'] = lib_dir + ':' + os.environ['PYTHONPATH']
            path.insert(int(path[0] == ''),lib_dir)
    #
    # Run the install
    #
    original_dir = getcwd()
    chdir(working_dir)
    command = [executable, 'setup.py', 'install', '--prefix={0}'.format(install_dir)]
    logger.debug(' '.join(command))
    if not options.test:
        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out, err = proc.communicate()
        logger.debug(out)
        if len(err) > 0:
            logger.error("Error during installation:")
            logger.error(err)
            return 1
    #
    # Process the module file.
    #
    module_file = join(working_dir,'etc',baseproduct+'.module')
    if exists(module_file):
        if options.moduledir == '':
            #
            # We didn't set a module dir, so derive it from options.root
            #
            if nersc is None:
                options.moduledir = join(options.root,'modulefiles')
            else:
                options.moduledir = join('/project/projectdirs/desi/software/modules',nersc)
            if not options.test:
                if not isdir(options.moduledir):
                    logger.info("Creating Modules directory {0}.".format(options.moduledir))
                    try:
                        makedirs(options.moduledir)
                    except OSError as ose:
                        logger.error(ose.strerror)
                        return 1
        if not options.test:
            if not isdir(join(options.moduledir,baseproduct)):
                try:
                    makedirs(join(options.moduledir,baseproduct))
                except OSError as ose:
                    logger.error(ose.strerror)
                    return 1
        install_module_file = join(options.moduledir,baseproduct,baseversion)
        with open(module_file) as m:
            mod = m.read().format(**module_keywords)
        if options.test:
            logger.debug(mod)
        else:
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
    # Build documentation
    #
    if options.documentation:
        if exists(join('doc','index.rst')):
            #
            # Assume Sphinx documentation.
            #
            sphinx_keywords = {
                'name':baseproduct,
                'release':baseversion,
                'version':'.'.join(baseversion.split('.')[0:3]),
                'year':datetime.date.today().year}
            for sd in ('_templates','_build','_static'):
                if not isdir(join('doc',sd)):
                    try:
                        makedirs(install_dir)
                    except OSError as ose:
                        logger.error(ose.strerror)
                        return 1
            if not exists(join('doc','Makefile')):
                copyfile(join(getenv('DESIUTIL_DIR'),'etc','doc','Makefile'),
                    join('doc','Makefile'))
            if not exists(join('doc','conf.py')):
                with open(join(getenv('DESIUTIL_DIR'),'etc','doc','Makefile')) as conf:
                    newconf = conf.read().format(**sphinx_keywords)
                with open(join('doc','conf.py'),'w') as conf2:
                    conf2.write(newconf)
            command = [executable, 'setup.py', 'build_sphinx']
            logger.debug(' '.join(command))
            if not options.test:
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                logger.debug(out)
                if len(err) > 0:
                    logger.error("Error during documentation build:")
                    logger.error(err)
                    return 1
            if isdir(join('build','html')):
                copytree(join('build','html'),join(install_dir,'doc'))
        else:
            logger.warn("Documentation build requested, but no documentation found.")

    #
    # Clean up
    #
    chdir(original_dir)
    rmtree(working_dir)
    return 0
#
#
#
if __name__ == '__main__':
    from sys import exit
    exit(main())
