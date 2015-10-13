==========
Change Log
==========

0.6.0 (unreleased)
------------------

* Fixed a problem with log handling.
* Use ``module switch`` instead of ``module load`` when a module is already
  loaded.
* Add changes.rst file.
* Migration to GitHub
  - Change case of desiutil.
  - Add git support files.
  - pip install support.
  - Travis build support.
  - ReadTheDocs support.

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
