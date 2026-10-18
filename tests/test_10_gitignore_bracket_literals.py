"""Test literal regex set operators in gitignore bracket expressions."""

import re
import unittest
import warnings

from pathspec import GitIgnoreSpec, PathSpec
from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
from pathspec.patterns.gitignore.spec import GitIgnoreSpecPattern
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

from .util import require_backend


CASES = (
	('[[]draft].md', ('[draft].md',), ('draft.md', 'adraft].md')),
	('[a&&b].pdf', ('a.pdf', '&.pdf', 'b.pdf'), ('c.pdf', 'ab.pdf')),
	('[a||b].pdf', ('a.pdf', '|.pdf', 'b.pdf'), ('c.pdf', 'ab.pdf')),
	('[a~~b].pdf', ('a.pdf', '~.pdf', 'b.pdf'), ('c.pdf', 'ab.pdf')),
	('[![]draft].md', ('adraft].md',), ('[draft].md', 'draft.md')),
	('[!a&&b].pdf', ('c.pdf',), ('a.pdf', '&.pdf', 'b.pdf')),
	('[^a||b].pdf', ('c.pdf',), ('a.pdf', '|.pdf', 'b.pdf')),
	('[!a~~b].pdf', ('c.pdf',), ('a.pdf', '~.pdf', 'b.pdf')),
	('[[:digit:]&&a-c].pdf', ('0.pdf', '&.pdf', 'b.pdf'), ('d.pdf', 'x.pdf')),
	(r'[\[\&\|\~].pdf', ('[.pdf', '&.pdf', '|.pdf', '~.pdf'), ('a.pdf',)),
	('[--0].pdf', ('-.pdf', '..pdf', '0.pdf'), ('1.pdf', '/.pdf')),
)


class BracketLiteralTest(unittest.TestCase):

	def test_pattern_literals(self):
		for factory in (GitIgnoreBasicPattern, GitIgnoreSpecPattern, GitWildMatchPattern):
			for line, matches, misses in CASES:
				for as_bytes in (False, True):
					for errors in (None, 'literal', 'null', 'raise'):
						with self.subTest(factory=factory, line=line, as_bytes=as_bytes, errors=errors):
							re.purge()
							with warnings.catch_warnings():
								warnings.simplefilter('ignore', DeprecationWarning)
								warnings.simplefilter('error', FutureWarning)
								pattern = factory(line.encode() if as_bytes else line, errors=errors)
							for paths, expected in ((matches, True), (misses, False)):
								for path in paths:
									self.assertEqual(
										bool(pattern.match_file(path.encode() if as_bytes else path)),
										expected, path,
									)

	def test_spec_literals(self):
		for backend in ('simple', 're2', 'hyperscan'):
			with self.subTest(backend=backend):
				require_backend(backend)
				for line, matches, misses in CASES:
					for style in ('gitignore', 'gitwildmatch', None):
						with self.subTest(line=line, style=style):
							re.purge()
							with warnings.catch_warnings():
								warnings.simplefilter('ignore', DeprecationWarning)
								warnings.simplefilter('error', FutureWarning)
								if style is None:
									spec = GitIgnoreSpec.from_lines([line], backend=backend)
								else:
									spec = PathSpec.from_lines(style, [line], backend=backend)
							for prefix in ('', 'docs/'):
								for paths, expected in ((matches, True), (misses, False)):
									for path in paths:
										self.assertEqual(spec.match_file(prefix + path), expected, path)
