
PathSpec
========

*pathspec* is a utility library for pattern matching of file paths. So far this
only includes Git's `gitignore`_ pattern matching.

.. _`gitignore`: http://git-scm.com/docs/gitignore


Tutorial
--------

Say you have a "Projects" directory and you want to back it up, but only
certain files, and ignore others depending on certain conditions::

	>>> from pathspec import PathSpec
	>>> # The gitignore-style patterns for files to select, but we're including
	>>> # instead of ignoring.
	>>> spec_text = """
	...
	... # This is a comment because the line begins with a hash: "#"
	...
	... # Include several project directories (and all descendants) relative to
	... # the current directory. To reference only a directory you must end with a
	... # slash: "/"
	... /project-a/
	... /project-b/
	... /project-c/
	...
	... # Patterns can be negated by prefixing with exclamation mark: "!"
	...
	... # Ignore temporary files beginning or ending with "~" and ending with
	... # ".swp".
	... !~*
	... !*~
	... !*.swp
	...
	... # These are python projects so ignore compiled python files from
	... # testing.
	... !*.pyc
	...
	... # Ignore the build directories but only directly under the project
	... # directories.
	... !/*/build/
	...
	... """

The ``PathSpec`` class provides an abstraction around pattern implementations,
and we want to compile our patterns as "gitignore" patterns. You could call it a
wrapper for a list of compiled patterns::

	>>> spec = PathSpec.from_lines('gitignore', spec_text.splitlines())

If we wanted to manually compile the patterns, we can use the ``GitIgnoreBasicPattern``
class directly. It is used in the background for "gitignore" which internally
converts patterns to regular expressions::

	>>> from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
	>>> patterns = map(GitIgnoreBasicPattern, spec_text.splitlines())
	>>> spec = PathSpec(patterns)

``PathSpec.from_lines()`` is a class method which simplifies that.

If you want to load the patterns from file, you can pass the file object
directly as well::

	>>> with open('patterns.list', 'r') as fh:
	>>>     spec = pathspec.PathSpec.from_lines('gitwildmatch', fh)

You can perform matching on a whole directory tree with::

	>>> matches = spec.match_tree_files('path/to/directory')

Or you can perform matching on a specific set of file paths with::

	>>> matches = spec.match_files(file_paths)

Or check to see if an individual file matches::

	>>> is_matched = spec.match_file(file_path)

There's actually two implementations of "gitignore". The basic implementation is
used by ``PathSpec`` and follows patterns as documented by `gitignore`_.
However, Git's behavior differs from the documented patterns. There's some
edge-cases, and in particular, Git allows including files from excluded
directories which appears to contradict the documentation. ``GitIgnoreSpec``
handles these cases to more closely replicate Git's behavior::

	>>> from pathspec import GitIgnoreSpec
	>>> spec = GitIgnoreSpec.from_lines(spec_text.splitlines())

You do not specify the style of pattern for ``GitIgnoreSpec`` because it should
always use ``GitIgnoreSpecPattern`` internally.


Performance
-----------

Running lots of regular expression matches against thousands of files in Python
is slow. Alternate regular expression backends can be used to improve
performance. ``PathSpec`` and ``GitIgnoreSpec`` both accept a ``backend``
parameter to control the backend. The default is "best" to automatically choose
the best available backend. There are currently 3 backends.

The "simple" backend is the default and it simply uses Python's ``re.Pattern``
objects that are normally created.

The "hyperscan" backend uses the `hyperscan`_ package. Hyperscan tends to be the
fastest between 1-15 patterns. At 1 pattern, it's 1.6 times faster than "simple"
and 1.2 times faster than "re2". At 15 patterns, it's 2.9 times faster than
"simple" and 1.1 times faster than "re2". At 100 patterns, it's 3.8 times faster
than "simple" and 0.4 times slower than "re2".

The "re2" backend uses the `google-re2`_ package. Re2 tends to be the fastest
with more than 15 patterns. At 1 pattern, it's 1.4 times faster than "simple"
and 0.9 times slower than "hyperscan". At 15 patterns, it's 2.6 times faster
than "simple" and 0.9 times slower than "hyperscan". At 100 patterns, it's 10
times faster than "simple" and 2.7 times faster than "hyperscan".


.. _`google-re2`: https://pypi.org/project/google-re2/
.. _`hyperscan`: https://pypi.org/project/hyperscan/


FAQ
---


1. How do I ignore files like *.gitignore*?
+++++++++++++++++++++++++++++++++++++++++++

``PathSpec`` (and ``GitIgnoreSpec`)) positively match files by default. To find
the files to keep, and exclude files like *.gitignore*, you need to set
``negate=True`` to flip the results::

	>>> from pathspec import GitIgnoreSpec
	>>> spec = GitIgnoreSpec.from_lines([...])
	>>> keep_files = spec.match_tree_files('path/to/directory', negate=True)


License
-------

*pathspec* is licensed under the `Mozilla Public License Version 2.0`_. See
`LICENSE`_ or the `FAQ`_ for more information.

In summary, you may use *pathspec* with any closed or open source project
without affecting the license of the larger work so long as you:

- give credit where credit is due,

- and release any custom changes made to *pathspec*.

.. _`Mozilla Public License Version 2.0`: http://www.mozilla.org/MPL/2.0
.. _`LICENSE`: LICENSE
.. _`FAQ`: http://www.mozilla.org/MPL/2.0/FAQ.html


Source
------

The source code for *pathspec* is available from the GitHub repo
`cpburnz/python-pathspec`_.

.. _`cpburnz/python-pathspec`: https://github.com/cpburnz/python-pathspec


Installation
------------

*pathspec* is available for install through `PyPI`_::

	pip install pathspec

*pathspec* can also be built from source. The following packages will be
required:

- `build`_ (>=0.6.0)

*pathspec* can then be built and installed with::

	python -m build
	pip install dist/pathspec-*-py3-none-any.whl

.. _`PyPI`: http://pypi.python.org/pypi/pathspec
.. _`build`: https://pypi.org/project/build/


Documentation
-------------

Documentation for *pathspec* is available on `Read the Docs`_.

.. _`Read the Docs`: https://python-path-specification.readthedocs.io


Other Languages
---------------

The related project `pathspec-ruby`_ (by *highb*) provides a similar library as
a `Ruby gem`_.

.. _`pathspec-ruby`: https://github.com/highb/pathspec-ruby
.. _`Ruby gem`: https://rubygems.org/gems/pathspec
