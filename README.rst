
*pathspec*: Path Specification
==============================

*pathspec* is a utility library for pattern matching of file paths. So
far this only includes `gitignore`_ style pattern matching which itself
incorporates POSIX `glob`_ patterns.

.. _`gitignore`: http://git-scm.com/docs/gitignore
.. _`glob`: http://man7.org/linux/man-pages/man7/glob.7.html


Tutorial
--------

Say you have a "Projects" directory and you want to back it up, but only
certain files, and ignore others depending on certain conditions.

  >>> import pathspec
  >>> # The gitignore-style patterns for files to select, but we're including
  >>> # instead of ignoring.
  >>> spec = """
  ...
  ... # This is a comment because the line begins with a hash: "#"
  ...
  ... # Include several project directories (and all descendants) relative to
  ... # the current directory. To reference a directory you must end with a
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

We want to use the ``GitIgnorePattern`` class to compile our patterns, and the
``PathSpec`` to provide an iterface around them:

  >>> spec = pathspec.PathSpec.from_lines(pathspec.GitIgnorePattern, spec.splitlines())

That may be a mouthful but it allows for additional patterns to be implemented
in the future without them having to deal with anything but matching the paths
sent to them. ``GitIgnorePattern`` is the implementation of the actual pattern
which internally gets converted into a regular expression. ``PathSpec`` is a
simple wrapper around a list of compiled patterns.

If we wanted to manually compile the patterns we can just do the following.

  >>> patterns = map(pathspec.GitIgnorePattern, spec.splitlines())
  >>> spec = PathSpec(patterns)

``PathSpec.from_lines()`` is simply a dumb class method to do just that.

If you want to load the patterns from file, you can pass the instance directly
as well.

  >>> with open('patterns.list', 'r') as fh:
  >>>     spec = pathspec.PathSpec.from_lines(pathspec.GitIgnorePattern, fh)



Source
------

The source code for *pathspec* is available from the GitHub repo
`cpburnz/python-path-specification`_.

.. _`cpburnz/python-path-specification`: https://github.com/cpburnz/python-path-specification


Installation
------------

*pathspec* requires the following packages:

- `setuptools`_

*pathspec* can be installed from source with::

	python setup.py install

*pathspec* is also available for install through `PyPI`_::

	pip install pathspec

.. _`setuptools`: https://pypi.python.org/pypi/setuptools
.. _`PyPI`: http://pypi.python.org/pypi/pathspec


.. image:: https://d2weczhvl823v0.cloudfront.net/cpburnz/python-path-specification/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free
