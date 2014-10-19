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

Product/Version Parsing
-----------------------

Because of the structure of the DESI code repository, it is sometimes necessary
to specify a directory name along with the product name.  desiInstall contains
a list of known products, but it is not necessarily complete. desiInstall parses
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

The downloaded code is scanned to determine the build type.  There are several
possible build types that are *not* mutually exclusive.

plain
    This is the default build type.  With this build type, the downloaded code
    is simply copied to the final install directory.
py
    If a setup.py file is detected, desiInstall will attempt to execute
    ``python setup.py install``.  This build type can be suppressed with the
    command line option ``--compile-c``.
make
    If a Makefile is detected, desiInstall will attempt to execute
    ``make install``.
src
    If a Makefile is not present, but a src/ directory is,
    desiInstall will attempt to execute ``make -C src all``.  This build type
    *is* mutually exclusive with 'make', but is not mutually exclusive with
    the other types.

**It is the responsibility of the code developer to ensure that these
build types do not conflict with each other.**

Determine Install Directory
---------------------------

The install directory is where the code will live permanently.  If the
install is taking place at NERSC, the install directory will be placed in
``/project/projectdirs/desi/software/${NERSC_HOST}``.

At other locations, the user must set the environment variable
``DESI_PRODUCT_ROOT`` to point to the equivalent directory.

If the install directory already exists, desiInstall will exit, unless the
``--force`` parameter is supplied on the command line.

desiInstall will set the environment variable ``INSTALL_DIR`` to point to the
install directory.

Module Infrastructure
---------------------

desiInstall sets up the Modules infrastructure by running ``execfile()`` on
the Python init file supplied by the Modules install.

Find Module File
----------------

desiInstall will search for a module file in ``$WORKING_DIR/etc``.  If that
module file is not found, desiInstall will use the file that comes with
desiUtil (*i.e.*, this product's own module file).

Load Dependencies
-----------------

desiInstall will scan the module file identified in the previous stage, and
will module load any dependencies found in the file.

Configure Module File
---------------------

desiInstall will scan ``$WORKING_DIR`` to determine the details that need
to be added to the module file.  The final module file will then be written
into the DESI module directory at NERSC or the module directory associated
with ``DESI_PRODUCT_ROOT``.  If ``--default`` is specified on the command
line, an approproate .version file will be created.

Load Module
-----------

desiInstall will load the module file just created to set up any environment
variables needed by the install.  At this point it is also safe to assume that
the environment variables ``WORKING_DIR`` and ``INSTALL_DIR`` exist.

Copy All Files
--------------

The entire contents of ``WORKING_DIR`` will be copied to ``INSTALL_DIR``.
If this is a trunk or branch install and a src/ directory is detected,
desiInstall will attempt to run ``make -C src all`` in ``$WORKING_DIR``.
For trunk or branch installs, no further processing is performed past this
point.

Create site-packages
--------------------

If the build-type 'py' is detected, a site-packages directory will be
created in ``INSTALL_DIR``.  If necessary, this directory will be
added to Python's ``sys.path``.

Run setup.py
------------

If the build-type 'py' is detected, ``python setup.py install`` will be run
at this point.

Documentation
-------------

Documentation will be built automatically unless one of these two conditions
exists:

* ``--no-documentation`` is specified on the command-line.
* This is a trunk or branch install.

If the build-type 'py' is detected, or even if just the py/ directory exists,
*and* a doc/index.rst file exists, desiInstall will attempt to build Sphinx
documentation.  The index.rst file is necessary to contain entry points to the
API documentation contained in the code itself.  The built documentation will
be placed in ``$INSTALL_DIR/doc/html``.

If the product appears to be primarily C/C++, and a doc/ directory exists,
desiInstall will construct the files needed to build Doxygen documentation.
However, the actual construction of the documentation is left up to the
top-level ``make install``.

Build C/C++ Code
----------------

If the build-type 'make' is detected, ``make install`` will be run in
``$WORKING_DIR``.  If the build-type 'src' is detected, ``make -C src all``
will be run in ``$INSTALL_DIR``.

Clean Up
--------

The original download directory, specified by ``WORKING_DIR``, is removed,
unless ``--keep`` is specified on the command line.
