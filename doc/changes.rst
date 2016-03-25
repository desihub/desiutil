==========
Change Log
==========

1.3.7 (unreleased)
------------------

1.3.6 (2016-03-25)
------------------

* Include funcfits in the documentation; added mk_fit_dict.
* Improve coverage of funcfits.
* Try to use a nicer Sphinx theme for documentation.

1.3.5 (2016-03-15)
------------------

* Ignore some additional MANIFEST.in warnings.
* Allow known_products and cross-install configuration to be overridden
  using an optional configuration file.
* Allow products to specify a method to download additional data not
  bundled with the code.

1.3.4 (2016-02-22)
------------------

* Support GitHub tags that start with 'v'.
* Add support for `speclite`_.

.. _`speclite`: https://github.com/dkirkby/speclite

1.3.3 (2016-02-03)
------------------

* Added :mod:`~desiutil.stats` module to compute percentiles on distributions.

1.3.2 (2016-01-25)
------------------

* Recent versions of setuptools do not include ``setuptools.compat``.  A
  simple workaround was added to fix that.

1.3.1 (2016-01-12)
------------------

* Update MANIFEST.in file.
* Ignore additional warnings produced by MANIFEST.in.
* Always run ``fix_permissions.sh`` after install.
* Remove references to defunct hopper system.

1.3.0 (2015-12-09)
------------------

* Updated docstrings for bitmasks.
* Added :mod:`~desuitil.funcfits` module.

1.2.0 (2015-11-24)
------------------

* Added bitmask processing code.
* Fixed a minor variable name bug.
* Ignore warnings produced by processing MANIFEST.in.
* Fixed return value in cross_install.
* Fixed a missing run stage.

1.1.1 (2015-11-18)
------------------

* Update the list of NERSC hosts, including cori.
* Code is now `PEP 8`_ compliant.

.. _`PEP 8`: http://legacy.python.org/dev/peps/pep-0008/

1.1.0 (2015-11-06)
------------------

* Don't print scary warning about :envvar:`DESI_PRODUCT_ROOT` not being
  set if running at NERSC.
* Support running ``python setup.py version`` in svn products.
* Move Modules support code into separate sub-package.
* Simplify Travis build system.
* Remove some obsolete files.
* Simplify package structure.

1.0.1 (2015-11-03)
------------------

* Fix issue where the Python tarfile package was failing to autodetect
  gzipped files.

1.0.0 (2015-10-29)
------------------

* pip install support.
* `Travis build support`_.
* `Read the Docs support`_.
* Remove unnecessary Sphinx extensions.
* Create setup subpackage for functions that go in setup.py files.
* fix_permissions.sh won't clobber executable bits.

.. _`Travis build support`: https://travis-ci.org/desihub/desiutil
.. _`Read the Docs support`: http://desiutil.readthedocs.org/en/latest/

0.6.0 (2015-10-13)
------------------

**Note:** This tag should not be used or installed.  It is an intermediate
tag intended to fix a subtle issue with how svn tags are translated into git
tags.

* Fixed a problem with log handling.
* Use ``module switch`` instead of ``module load`` when a module is already
  loaded.
* Add changes.rst file.
* Add LICENSE.rst file.
* Migration to GitHub
  - Change case of desiutil.
  - Add git support functions.

0.5.5 (2015-01-16)
------------------

* Fix a corner case when desiInstall tries to install desiUtil.
* Fix an svn version string parsing error.

0.5.4 (2015-01-16)
------------------

* Fix a minor syntax error.

0.5.3 (2015-01-16)
------------------

* Fix a minor syntax error.

0.5.2 (2015-01-16)
------------------

* Update desiInstall documentation.
* Changes to doc compilation.

0.5.1 (2015-01-14)
------------------

* Update desiInstall documentation.
* Handle ``-hpcp`` module names.
* Move build type detection to separate function.
* Move documentation generation to separate function.
* Add cross-install support.

0.5.0 (2015-01-14)
------------------

* Adding support for GitHub installs.

0.4.2 (2015-01-12)
------------------

* Fix a minor syntax error.

0.4.1 (2015-01-12)
------------------

* Fix a minor syntax error.

0.4.0 (2015-01-12)
------------------

* Major refactor of install, support 'plain' products.
* Use ``svn --non-interactive`` where possible.

0.3.9 (2014-09-12)
------------------

* Change the way tags are sorted.
* Tweak documentation compilation.

0.3.8 (2014-06-24)
------------------

* Change severity of certain log messages.

0.3.7 (2014-06-24)
------------------

* Minor fix to logging.

0.3.6 (2014-06-24)
------------------

* Don't auto-generate the desiInstall script.

0.3.5 (2014-06-24)
------------------

* Use ez_setup.py.

0.3.4 (2014-06-23)
------------------

* Reconfigure how the desiInstall script is created.

0.3.3 (2014-06-23)
------------------

* Tweak module file detection.

0.3.2 (2014-06-23)
------------------

* Fix chmod error.

0.3.1 (2014-06-23)
------------------

* Change ``version()`` to ``__version__``.

0.3.0 (2014-06-10)
------------------

* Change how version strings are set.
* Auto-detect a variety of build types.

0.2.5 (2014-05-26)
------------------

* Fix how the Modules Python init file is detected.

0.2.4 (2014-05-06)
------------------

* Fix directory creation for trunk/branch installs.

0.2.3 (2014-05-02)
------------------

* Change how dependencies are handled in the module file.
* Move some dependency processing to separate function.
* General restructuring.

0.2.2 (2014-05-01)
------------------

* Copy extra files in the etc directory.
* Remove some data files from setup.py.

0.2.1 (2014-05-01)
------------------

* Tweak how versions are reported.

0.2.0 (2014-05-01)
------------------

* Tweak documentation.
* Add ACL detection to fix_permission script.

0.1 (2014-01-09)
----------------

* First tag.
