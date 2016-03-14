===========
desiInstall
===========

Introduction
============

This document describes the desiInstall process and the logic behind it.

Configuring desiInstall
=======================

desiInstall has many options, which are best viewed by typing
``desiInstall -h``.

In addition, it is possible to override certain internal settings of
the :class:`~desiutil.install.DesiInstall` object using an
INI-style configuration file, supplying the name of the file with the
``--configuration`` option.  Here is an example of the contents of such
file::

    #
    # READ ME FIRST
    #
    # This file provides an example of how to override certain internal settings
    # in desiInstall (desiutil.install).  You can copy this file, edit your copy
    # and supply it to desiInstall with the --configuration option.
    #
    #
    # This section can be used to override built-in names of NERSC hosts.
    # Specifically, these will override the cross_install_host and
    # nersc_hosts attributes of the DesiInstall object.
    #
    [Cross Install]
    cross_install_host = cori
    nersc_hosts = cori,edison,datatran
    #
    # This section can be used to append to or override values in the
    # known_products dictionary in desiutil.install.
    #
    [Known Products]
    my_new_product = https://github.com/me/my_new_product
    desiutil = https://github.com/you/new_path_to_desiutil

Stages of the Install
=====================

Input Validation
----------------

desiInstall checks the command-line input, verifying that the user has
specified a product and a version to install.

Product/Version Parsing
-----------------------

Because of the structures of the DESI code repositories, it is sometimes necessary
to specify a directory name along with the product name.  desiInstall contains
a list of known products, but it is not necessarily complete. desiInstall parses
the input to determine the base name and base version to install.  At this
stage desiInstall also determines whether a trunk or branch install has
been requested.

Product Existence
-----------------

After the product name and version have been determined, desiInstall
constructs the full URL pointing to the product/version and runs the code
necessary to verify that the product/version really exists.  Typically, this
will be ``svn ls``, unless a GitHub install is detected.

Download Code
-------------

The code is downloaded, using ``svn export`` for standard (tag) installs, or
``svn checkout`` for trunk or branch installs.  For GitHub installs, desiInstall
will look for a release tarball, or do a ``git clone`` for tag or master/branch
installs.  desiInstall will set the environment variable :envvar:`WORKING_DIR`
to point to the directory containing this downloaded code.

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
:envvar:`DESI_PRODUCT_ROOT` to point to the equivalent directory.

If the install directory already exists, desiInstall will exit, unless the
``--force`` parameter is supplied on the command line.

desiInstall will set the environment variable :envvar:`INSTALL_DIR` to point to the
install directory.

Module Infrastructure
---------------------

desiInstall sets up the Modules infrastructure by running ``execfile()`` on
the Python init file supplied by the Modules install.

Find Module File
----------------

desiInstall will search for a module file in ``$WORKING_DIR/etc``.  If that
module file is not found, desiInstall will use the file that comes with
desiutil (*i.e.*, this product's own module file).

Load Dependencies
-----------------

desiInstall will scan the module file identified in the previous stage, and
will module load any dependencies found in the file.  desiInstall will
purge modules whose name contains ``-hpcp`` if it detects it is not running
at NERSC.  Similarly, it will purge modules *not* containing ``-hpcp`` if
it detects a NERSC environment.

Configure Module File
---------------------

desiInstall will scan :envvar:`WORKING_DIR` to determine the details that need
to be added to the module file.  The final module file will then be written
into the DESI module directory at NERSC or the module directory associated
with :envvar:`DESI_PRODUCT_ROOT`.  If ``--default`` is specified on the command
line, an approproate .version file will be created.

Load Module
-----------

desiInstall will load the module file just created to set up any environment
variables needed by the install.  At this point it is also safe to assume that
the environment variables :envvar:`WORKING_DIR` and :envvar:`INSTALL_DIR` exist.
It will also set :envvar:`PRODUCT_VERSION`, where ``PRODUCT`` will be replaced
by the actual name of the package, *e.g.*, :envvar:`DESIMODEL_VERSION`.

Download Extra Data
-------------------

If desiInstall detects ``etc/product_data.sh``, where ``product`` should be
replaced by the actual name of the package, it will download extra data
not bundled with the code, so that it can be installed in
:envvar:`INSTALL_DIR` in the next stage.

Copy All Files
--------------

The entire contents of :envvar:`WORKING_DIR` will be copied to :envvar:`INSTALL_DIR`.
If this is a trunk or branch install and a src/ directory is detected,
desiInstall will attempt to run ``make -C src all`` in :envvar:`INSTALL_DIR`.
For trunk or branch installs, no further processing is performed past this
point.

Create site-packages
--------------------

If the build-type 'py' is detected, a site-packages directory will be
created in :envvar:`INSTALL_DIR`.  If necessary, this directory will be
added to Python's ``sys.path``.

Run setup.py
------------

If the build-type 'py' is detected, ``python setup.py install`` will be run
at this point.

Build C/C++ Code
----------------

If the build-type 'make' is detected, ``make install`` will be run in
:envvar:`WORKING_DIR`.  If the build-type 'src' is detected, ``make -C src all``
will be run in :envvar:`INSTALL_DIR`.

Cross Install
-------------

If the ``--cross-install`` option is specified, and the NERSC environment is
detected, symlinks will be created to make the package available on all
NERSC platforms.

Clean Up
--------

The original download directory, specified by :envvar:`WORKING_DIR`, is removed,
unless ``--keep`` is specified on the command line.
