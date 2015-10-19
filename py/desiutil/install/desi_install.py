# Licensed under a 3-clause BSD style license - see LICENSE.rst
# -*- coding: utf-8 -*-
"""Install DESI software.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
import logging
from os.path import basename
from sys import argv
#
#
#
class DesiInstall(object):
    """Code and data that drive the desiInstall script.
    """
    def __init__(self):
        xct = basename(argv[0])
        # debug = options.test or options.verbose
        ll = logging.INFO
        # if debug:
        #     ll = logging.DEBUG
        logging.basicConfig(level=ll, format=xct+' [%(name)s] Log - %(levelname)s: %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
        log = logging.getLogger('desiInstall.__init__')
        log.info('foo')
        return
    def run(self):
        log = logging.getLogger('desiInstall.run')
        log.info('bar')
        self.frobulate()
        return 0
    def frobulate(self):
        log = logging.getLogger('desiInstall.frobulate')
        log.warn('frob')
        return
#
#
#
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
    di = DesiInstall()
    status = di.run()
    return status
