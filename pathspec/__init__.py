# encoding: utf-8
"""
The *pathspec* package provides pattern matching for file paths. So far
this only includes gitignore style pattern matching.

See "README.rst" or <https://github.com/cpburnz/python-path-specification>
for more information. Or you can always scour the source code.
"""
from __future__ import unicode_literals

__author__ = "Caleb P. Burns"
__copyright__ = "Copyright © 2013-2016 Caleb P. Burns"
__created__ = "2013-10-12"
__credits__ = [
	"dahlia <https://github.com/dahlia>",
	"highb <https://github.com/highb>",
	"029xue <https://github.com/029xue>",
	"mikexstudios <https://github.com/mikexstudios>",
	"nhumrich <https://github.com/nhumrich>",
	"davidfraser <https://github.com/davidfraser>",
]
__email__ = "cpburnz@gmail.com"
__license__ = "MPL 2.0"
__project__ = "pathspec"
__status__ = "Development"
__updated__ = "2016-07-15"
__version__ = "0.4.0"

from .gitignore import GitIgnorePattern
from .pathspec import PathSpec
from .pattern import Pattern, RegexPattern
from .util import iter_tree, match_files, RecursionError
