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
    from os import chdir, chmod, environ, getcwd, getenv, makedirs, remove, stat, symlink, walk
    from os.path import abspath, basename, exists, isdir, islink, join
    from urllib2 import urlopen, HTTPError
    from argparse import ArgumentParser
    from .. import __version__ as desiUtilVersion
    from . import dependencies, generate_doc, get_product_version, most_recent_tag, set_build_type
    #
    # Parse arguments
    #
    xct = basename(argv[0])
    parser = ArgumentParser(description=__doc__,prog=xct)
    parser.add_argument('-b', '--bootstrap', action='store_true', dest='bootstrap',
        help="Run in bootstrap mode to install the desiUtil product.")
    parser.add_argument('-C', '--compile-c', action='store_true', dest='force_build_type',
        help="Force C/C++ install mode, even if a setup.py file is detected (WARNING: this is for experts only).")
    parser.add_argument('-d', '--default', action='store_true', dest='default',
        help='Make this version the default version.')
    parser.add_argument('-D', '--no-documentation', action='store_false', dest='documentation',
        help='Do NOT build any Sphinx or Doxygen documentation.')
    parser.add_argument('-F', '--force', action='store_true', dest='force',
        help='Overwrite any existing installation of this product/version.')
    parser.add_argument('-k', '--keep', action='store_true', dest='keep',
        help='Keep the exported build directory.')
    parser.add_argument('-m', '--module-home', action='store', dest='moduleshome',
        metavar='DIR',help='Set or override the value of $MODULESHOME',
        default=getenv('MODULESHOME'))
    parser.add_argument('-M', '--module-dir', action='store', dest='moduledir',
        metavar='DIR',help="Install module files in DIR.",default='')
    parser.add_argument('-p', '--python', action='store', dest='python',
        metavar='PYTHON',help="Use the Python executable PYTHON (e.g. /opt/local/bin/python2.7).  This option is only relevant when installing desiUtil itself.")
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
    parser.add_argument('-V', '--version', action='version',
        version='%(prog)s '+desiUtilVersion)
    parser.add_argument('-x', '--cross-install', action='store_true', dest='cross_install',
        help='Make the install available on multiple systems (e.g. NERSC).')
    parser.add_argument('product',nargs='?',default='NO PACKAGE',
        help='Name of product to install.')
    parser.add_argument('product_version',nargs='?',default='NO VERSION',
        help='Version of product to install.')
    options = parser.parse_args()
    #
    # Set up logger
    #
    debug = options.test or options.verbose
    logger = logging.getLogger(__name__)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(xct+' (%(name)s) Log - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    #
    # Sanity check options
    #
    if options.product == 'NO PACKAGE' or options.product_version == 'NO VERSION':
        if options.bootstrap:
            options.default = True
            options.product = 'tools/desiUtil'
            options.product_version = most_recent_tag(join(options.url,options.product,'tags'),username=options.username)
            logger.info("Selected desiUtil/{0} for installation.".format(options.product_version))
        else:
            logger.error("You must specify a product and a version!")
            return 1
    if options.moduleshome is None or not isdir(options.moduleshome):
        logger.error("You do not appear to have Modules set up.")
        return 1
    github = False
    if 'github' in options.url:
        github = True
        logger.debug("Detected GitHub install.")
    #
    # Determine the product and version names.
    #
    try:
        fullproduct, baseproduct, baseversion = get_product_version(options)
    except KeyError:
        return 1
    is_branch = options.product_version.startswith('branches')
    is_trunk = options.product_version == 'trunk' or options.product_version == 'master'
    if is_trunk or is_branch:
        if github:
            product_url = join(options.url,fullproduct)+'.git'
        else:
            product_url = join(options.url,fullproduct,baseproduct)
    else:
        if github:
            product_url = join(options.url,fullproduct,'archive',options.product_version+'.tar.gz')
        else:
            product_url = join(options.url,fullproduct,'tags',options.product_version)
    logger.debug("Using {0} as the URL of this product.".format(product_url))
    #
    # Check for existence of the URL.
    #
    if not github:
        command = ['svn','--non-interactive','--username',options.username,'ls',product_url]
        logger.debug(' '.join(command))
        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out, err = proc.communicate()
        logger.debug(out)
        if len(err) > 0:
            logger.error("svn error while testing product URL:")
            logger.error(err)
            return 1
    #
    # Get the code
    #
    working_dir = join(abspath('.'),'{0}-{1}'.format(baseproduct,baseversion))
    if isdir(working_dir):
        logger.info("Detected old working directory, {0}. Deleting...".format(working_dir))
        rmtree(working_dir)
    if github:
        if is_trunk or is_branch:
            if is_branch:
                try:
                    f = urlopen(join(options.url,fullproduct,'tree',baseversion))
                except HTTPError as e:
                    logger.error("Branch {0} does not appear to exist. HTTP response was {1:d}.".format(baseversion,e.code))
                    return 1
            command = ['git', 'clone', '-q', product_url, working_dir]
            logger.debug(' '.join(command))
            proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = proc.communicate()
            logger.debug(out)
            if len(err) > 0:
                logger.error("git error while downloading product code:")
                logger.error(err)
                return 1
            if is_branch:
                original_dir = getcwd()
                chdir(working_dir)
                command = ['git', 'checkout', '-q', '-b', baseversion, 'origin/'+baseversion]
                logger.debug(' '.join(command))
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                logger.debug(out)
                if len(err) > 0:
                    logger.error("git error while changing branch:")
                    logger.error(err)
                    return 1
                chdir(original_dir)
        else:
            try:
                u = urlopen(product_url)
                tgz = u.read()
            except HTTPError as e:
                logger.error("Error while downloading {0}, HTTP response was {1:d}.".format(product_url,e.code))
                return 1
            u.close()
            with open(options.product_version+'.tar.gz','w') as u:
                u.write(tgz)
            command = ['tar', '-xzf', options.product_version+'.tar.gz']
            logger.debug(' '.join(command))
            proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = proc.communicate()
            logger.debug(out)
            if len(err) > 0:
                logger.error("tar error while expanding product code:")
                logger.error(err)
                return 1
            remove(options.product_version+'.tar.gz')
    else:
        if is_trunk or is_branch:
            get_svn = 'checkout'
        else:
            get_svn = 'export'
        command = ['svn','--non-interactive','--username',options.username,get_svn,product_url,working_dir]
        logger.debug(' '.join(command))
        proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out, err = proc.communicate()
        logger.debug(out)
        if len(err) > 0:
            logger.error("svn error while downloading product code:")
            logger.error(err)
            return 1
    #
    # Analyze the code to determine the build type
    #
    build_type = set_build_type(working_dir,options.force_build_type)
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
    if options.root is not None:
        environ['DESI_PRODUCT_ROOT'] = options.root
    install_dir = join(options.root,baseproduct,baseversion)
    if isdir(install_dir) and not options.test:
        if options.force:
            rmtree(install_dir)
        else:
            logger.error("Install directory, {0}, already exists!".format(install_dir))
            return 1
    #
    # If this is a trunk or branch install, this directory will be created
    # by other means.
    #
    # if not (is_branch or is_trunk or options.test):
    #     try:
    #         makedirs(install_dir)
    #     except OSError as ose:
    #         logger.error(ose.strerror)
    #         return 1
    #
    # Store the value of the Python executable, if set.  This is not
    # necessary to do because the setup.py process will convert the
    # script.
    #
    # if options.product == 'tools/desiUtil' and options.python is not None:
    #     desiInstall = join(working_dir,'bin','desiInstall')
    #     mode = stat(desiInstall).st_mode
    #     with open(desiInstall) as i:
    #         l = i.readlines()
    #     l[0] = "#!{0}\n".format(options.python)
    #     with open(desiInstall,'w') as i:
    #         i.write(''.join(l))
    #     chmod(desiInstall,mode)
    #
    # Set up Modules
    #
    initpy_found = False
    for modpy in ('python','python.py'):
        initpy = join(options.moduleshome,'init',modpy)
        if exists(initpy):
            initpy_found = True
            execfile(initpy,globals())
    if not initpy_found:
        logger.error("Could not find the Python file in {0}/init!".format(options.moduleshome))
        return 1
    #
    # Figure out dependencies by reading the unprocessed module file
    #
    module_file = join(working_dir,'etc',baseproduct+'.module')
    if not exists(module_file):
        module_file = join(getenv('DESIUTIL'),'etc','desiUtil.module')
    deps = dependencies(module_file)
    for d in deps:
        logger.debug("module('load','{0}')".format(d))
        module('load',d)
    #
    # Prepare to configure module.
    #
    module_keywords = {
        'name': baseproduct,
        'version': baseversion,
        'needs_bin': '# ',
        'needs_python': '# ',
        'needs_trunk_py': '# ',
        'needs_ld_lib': '# ',
        'needs_idl': '# ',
        'pyversion': "python{0:d}.{1:d}".format(*version_info)
        }
    if isdir(join(working_dir,'bin')):
        module_keywords['needs_bin'] = ''
    if isdir(join(working_dir,'lib')):
        module_keywords['needs_ld_lib'] = ''
    if isdir(join(working_dir,'pro')):
        module_keywords['needs_idl'] = ''
    if 'py' in build_type:
        if is_branch or is_trunk:
            module_keywords['needs_trunk_py'] = ''
        else:
            module_keywords['needs_python'] = ''
    else:
        if isdir(join(working_dir,'py')):
            module_keywords['needs_trunk_py'] = ''
    #
    # Process the module file.
    #
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
    # Set up some convenient environment variables.
    #
    environ['WORKING_DIR'] = working_dir
    environ['INSTALL_DIR'] = install_dir
    logger.debug("module('load','{0}/{1}')".format(baseproduct,baseversion))
    module('load',baseproduct+'/'+baseversion)
    original_dir = getcwd()
    #
    # Start the install by simply copying the files.
    #
    logger.debug("copytree('{0}','{1}')".format(working_dir,install_dir))
    if not options.test:
        copytree(working_dir,install_dir)
    #
    # Handle trunk or branch installs.
    #
    if (is_trunk or is_branch):
        if 'src' in build_type:
            chdir(install_dir)
            command = ['make','-C', 'src', 'all']
            logger.info('Running "{0}" in {1}.'.format(' '.join(command),install_dir))
            proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = proc.communicate()
            logger.debug(out)
            if len(err) > 0:
                logger.error("Error during compile:")
                logger.error(err)
                return 1
        if options.documentation:
            logger.warn('Documentation will not be built automatically for trunk or branch installs!')
            logger.warn('You can use the desiDoc script to build documentation on your own.')
    else:
        #
        # Run a 'real' install
        #
        chdir(working_dir)
        if 'py' in build_type:
            #
            # For Python installs, a site-packages directory needs to exist.
            # We may need to manipulate sys.path to include this directory.
            #
            lib_dir = join(install_dir,'lib',module_keywords['pyversion'],'site-packages')
            if not options.test:
                try:
                    makedirs(lib_dir)
                except OSError as ose:
                    logger.error(ose.strerror)
                    return 1
                if lib_dir not in path:
                    try:
                        newpythonpath = lib_dir + ':' + environ['PYTHONPATH']
                    except KeyError:
                        newpythonpath = lib_dir
                    environ['PYTHONPATH'] = newpythonpath
                    path.insert(int(path[0] == ''),lib_dir)
            #
            # Ready to python setup.py
            #
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
        # Build documentation
        #
        if options.documentation:
            status = generate_doc(working_dir,install_dir,options)
            if status != 0:
                return status
        #
        # At this point either we have already completed a Python installation
        # or we still need to compile the C/C++ product (we had to construct
        # doc/Makefile first).
        #
        if 'make' in build_type or 'src' in build_type:
            if 'src' in build_type:
                chdir(install_dir)
                command = ['make','-C', 'src', 'all']
            else:
                command = ['make', 'install']
            logger.debug(' '.join(command))
            if not options.test:
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                logger.debug(out)
                if len(err) > 0:
                    logger.error("Error during compile:")
                    logger.error(err)
                    return 1
        #
        # Link documentation into www directory at NERSC
        #
        if options.documentation:
            if nersc is None:
                logger.debug("Skipping installation into www directory.")
            else:
                www_dir = join('/project/projectdirs/desi/www/doc',baseproduct))
                if not isdir(www_dir):
                    makedirs(www_dir)
                doc_dir = join(install_dir,'doc','html')
                if islink(join(www_dir,baseversion)):
                    logger.warning("Documentation for {0}/{1} already exists.".format(baseproduct,baseversion))
                else:
                    if isdir(doc_dir):
                        logger.debug("symlink('{0}','{1}')".format(doc_dir,join(www_dir,baseversion))
                        symlink(doc_dir,join(www_dir,baseversion))
    #
    # Cross-install this product at NERSC.
    #
    if options.cross_install:
        if nersc is None:
            logger.warning("Cross-installs are only supported at NERSC.")
        elif nersc != 'edison':
            logger.warning("Cross-installs should be performed on edison.")
        else:
            for nh in ('carver','hopper','datatran','scigate'):
                if not islink(join('/project/projectdirs/desi/software',nh,baseproduct)):
                    logger.debug("symlink('../edison/{0}','/project/projectdirs/desi/software/{1}/{0}')".format(baseproduct,nh))
                    symlink(join('..','edison',baseproduct),join('/project/projectdirs/desi/software',nh,baseproduct))
                if not islink(join('/project/projectdirs/desi/software/modules',nh,baseproduct)):
                    logger.debug("symlink('../edison/{0}','/project/projectdirs/desi/software/modules/{1}/{0}')".format(baseproduct,nh))
                    symlink(join('..','edison',baseproduct),join('/project/projectdirs/desi/modules/software',nh,baseproduct))
    #
    # Clean up
    #
    chdir(original_dir)
    if not options.keep:
        rmtree(working_dir)
    return 0
#
#
#
if __name__ == '__main__':
    from sys import exit
    exit(main())
