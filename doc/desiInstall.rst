===========
desiInstall
===========

Introduction
============

This document describes the desiInstall process and the logic behind it.

Stages of the Install
=====================

Input Validation
----------------

desiInstall checks the command-line input, verifying that the user has
specified a product and a version to install.

Module Infrastructure
---------------------

desiInstall sets up the Modules infrastructure by running ``execfile()`` on
the Python init file supplied by the Modules install.

Product/Version Parsing
-----------------------

Because of the structure of the DESI code repository, it is sometimes necessary
to specify a directory name along with the product name.  desiInstall parses
the input to determine the base name and base version to install.  At this
stage desiInstall also determines whether a trunk or branch install has
been requested.

Product Existence
-----------------

After the product name and version have been determined, desiInstall
constructs the full URL pointing to the product/version and runs ``svn ls`` to
verify that the product/version really exists.

Download Code
-------------

The code is downloaded, using ``svn export`` for standard (tag) installs, or
``svn checkout`` for trunk or branch installs.  desiInstall will set the
environment variable ``WORKING_DIR`` to point to the directory containing
this downloaded code.

Determine Build Type
--------------------

The downloaded code is scanned to determine the build type.  There are three
possible build types that are *not* mutually exclusive.

plain
    This is the default build type.  With this build type, the downloaded code
    is simply copied to the final install directory.
py
    If a setup.py file is detected, desiInstall will attempt to execute
    ``python setup.py install``.  This build type can be suppressed with the
    command line option ``--compile-c``.
c
    If a Makefile is detected, desiInstall will attempt to execute
    ``make install``.  If a Makefile is not present, but a src/ directory is,
    desiInstall will attempt to execute ``make -C src all``.

**It is the responsibility of the code developer to ensure that these
build types do not conflict with each other.**

Determine Install Directory
---------------------------

The install directory is where the code will live permanently.  If the
install is taking place at NERSC, the install directory will be placed in::

    /project/projectdirs/desi/software/${NERSC_HOST}.

At other locations, the user must set the environment variable
``DESI_PRODUCT_ROOT`` to point to the equivalent directory.

If the install directory already exists, desiInstall will exit, unless the
``--force`` parameter is supplied on the command line.

desiInstall will set the environment variable ``INSTALL_DIR`` to point to the
install directory.

Find Module File
----------------

desiInstall will search for a module file in ``$WORKING_DIR/etc``.  If that
module file is not found, desiInstall will use the file that comes with
desiUtil (*i.e.*, this product's own module file).

Load Dependencies
-----------------

desiInstall will scan the module file identified in the previous stage, and
will module load and dependencies found in the file.

Configure Module File
---------------------

desiInstall will scan ``$WORKING_DIR`` to determine the details that need
to be added to the module file.  The final module file will then be written
into the DESI module directory at NERSC or the module directory associated
with ``DESI_PRODUCT_ROOT``.  If ``--default`` is specified on the command
line, an approproate .version file will be created.
