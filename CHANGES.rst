
Change History
==============

0.5.3 (TBD)
-----------

- Include "LICENSE" in source package.
- Support Python 2.6.
- Issue #14: Fix byte strings for Python 3.


0.5.2 (2017-04-04)
------------------

- Fixed change log.


0.5.1 (2017-04-04)
------------------

- Issue #13: Add equality methods to `PathSpec` and `RegexPattern`.


0.5.0 (2016-08-22)
------------------

- Issue #12: Add `PathSpec.match_file()`.
- Renamed `gitignore.GitIgnorePattern` to `patterns.gitwildmatch.GitWildMatchPattern`.
- Deprecated `gitignore.GitIgnorePattern`.


0.4.0 (2016-07-15)
------------------

- Issue #11: Support converting patterns into regular expressions without compiling them.
- API change: Subclasses of `RegexPattern` should implement `pattern_to_regex()`.


0.3.4 (2015-08-24)
------------------

- Issue #7: Fixed non-recursive links.
- Issue #8: Fixed edge cases in gitignore patterns.
- Issue #9: Fixed minor usage documentation.
- Fixed recursion detection.
- Fixed trivial incompatibility with Python 3.2.


0.3.3 (2014-11-21)
------------------

- Improved documentation.


0.3.2 (2014-11-08)
------------------

- Improved documentation.
- Issue #6: Fixed matching Windows paths.
- API change: `spec.match_tree()` and `spec.match_files()` now return iterators instead of sets.


0.3.1 (2014-09-17)
------------------

- Updated README.


0.3.0 (2014-09-17)
------------------

- Added registered patterns.
- Issue #3: Fixed trailing slash in gitignore patterns.
- Issue #4: Fixed test for trailing slash in gitignore patterns.


0.2.2 (2013-12-17)
------------------

- Fixed setup.py.


0.2.1 (2013-12-17)
------------------

- Added tests.
- Fixed comment gitignore patterns.
- Fixed relative path gitignore patterns.


0.2.0 (2013-12-07)
------------------

- Initial release.
