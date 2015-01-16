# License information goes here
# -*- coding: utf-8 -*-
"""Generate documentation for DESI software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
def generate_doc(working_dir,install_dir=None,options=None):
    """Generate documentation.

    Parameters
    ----------
    working_dir : str
        Name of the working directory.
    install_dir : str, optional
        Name of the install directory.
    options : Namespace
        Options object generated by argparse.

    Returns
    -------
    generate_doc : int
        Exit status that will be passed to ``sys.exit()``.
    """
    import logging
    import subprocess
    from sys import executable
    from datetime import date
    from os import getenv, makedirs
    from os.path import exists, isdir, join
    from shutil import copyfile, copytree
    from . import get_product_version, set_build_type
    logger = logging.getLogger(__name__)
    if options is None:
        logger.error("options parameter is not set!")
        return 1
    build_type = set_build_type(working_dir,options.force_build_type)
    logger.debug(str(build_type))
    try:
        fullproduct, baseproduct, baseversion = get_product_version(options)
    except KeyError:
        return 1
    if 'py' in build_type or isdir('py'):
        if exists(join('doc','index.rst')):
            #
            # Assume Sphinx documentation.
            #
            sphinx_dir = join(getenv('DESIUTIL'),'etc','doc','sphinx')
            sphinx_keywords = {
                'name':baseproduct,
                'release':baseversion,
                'version':'.'.join(baseversion.split('.')[0:3]),
                'year':date.today().year}
            for sd in ('_build','_static'):
                if not isdir(join('doc',sd)):
                    try:
                        makedirs(join('doc',sd))
                    except OSError as ose:
                        logger.error(ose.strerror)
                        return 1
            if not exists(join('doc','Makefile')):
                copyfile(join(sphinx_dir,'Makefile'),join('doc','Makefile'))
            if not exists(join('doc','conf.py')):
                with open(join(sphinx_dir,'conf.py')) as conf:
                    newconf = conf.read().format(**sphinx_keywords)
                with open(join('doc','conf.py'),'w') as conf2:
                    conf2.write(newconf)
            if not exists(join('doc','_templates')):
                copytree(join(sphinx_dir,'_templates'),join('doc','_templates'))
            command = [executable, 'setup.py', 'build_sphinx', '--fresh-env', '--all-files']
            logger.debug(' '.join(command))
            if not options.test:
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                logger.debug(out)
                if len(err) > 0:
                    logger.error("Error during documentation build:")
                    logger.error(err)
                    return 1
            if not options.test and install_dir is not None:
                if isdir(join('build','sphinx','html')):
                    copytree(join('build','sphinx','html'),join(install_dir,'doc','html','sphinx'))
        else:
            logger.warn("Documentation build requested, but no documentation found.")
    #
    # Look for Doxygen documentation.
    #
    if 'make' in build_type:
        if isdir('doc'):
            doxygen_keywords = {
                'name':baseproduct,
                'version':baseversion,
                'description':"Documentation for {0} built by desiInstall.".format(baseproduct)}
            if not exists(join('doc','Doxygen.Makefile')):
                copyfile(join(getenv('DESIUTIL'),'etc','doc','doxygen','Makefile'),
                    join('doc','Doxygen.Makefile'))
            if not exists(join('doc','Doxyfile')):
                with open(join(getenv('DESIUTIL'),'etc','doc','doxygen','Doxyfile')) as conf:
                    newconf = conf.read().format(**doxygen_keywords)
                with open(join('doc','Doxyfile'),'w') as conf2:
                    conf2.write(newconf)
            command = ['make', '-C', 'doc', '-f', 'Doxygen.Makefile', 'all']
            logger.debug(' '.join(command))
            if not options.test:
                proc = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                out, err = proc.communicate()
                logger.debug(out)
                if len(err) > 0:
                    logger.error("Error during compile:")
                    logger.error(err)
                    return 1
        else:
            logger.warn("Documentation build requested, but no documentation found.")
    return 0
#
#
#
def main():
    """Call this program from a command-line script.

    Parameters
    ----------
    None

    Returns
    -------
    main : int
        Exit status that will be passed to ``sys.exit()``.
    """
    import logging
    from sys import argv
    from os import getcwd
    from os.path import basename
    from argparse import ArgumentParser
    from .. import __version__ as desiUtilVersion
    #
    # Parse arguments
    #
    xct = basename(argv[0])
    parser = ArgumentParser(description=__doc__,prog=xct)
    parser.add_argument('-C', '--compile-c', action='store_true', dest='force_build_type',
        help="Force C/C++ install mode, even if a setup.py file is detected (WARNING: this is for experts only).")
    parser.add_argument('-t', '--test', action='store_true', dest='test',
        help='Test mode.  Do not actually install anything.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
        help='Print extra information.')
    parser.add_argument('-V', '--version', action='version',
        version='%(prog)s '+desiUtilVersion)
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
    # Build documentation
    #
    working_dir = getcwd()
    status = generate_doc(working_dir,None,options)
    return status
