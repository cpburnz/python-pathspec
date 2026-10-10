# pyright: strict

from pathspec import (
	PathSpec,
	GitIgnoreSpec)
from pathspec.patterns.gitignore.basic import (
	GitIgnoreBasicPattern)
from pathspec.patterns.gitignore.spec import (
	GitIgnoreSpecPattern)


def check_gi_1():
	spec = GitIgnoreSpec.from_lines(['**'])
	return spec


def check_gi_2():
	pattern = 'gitignore'
	spec = GitIgnoreSpec.from_lines(pattern, ['**'])
	return spec


def check_gi_3():
	pattern = 'gitignore'
	spec = GitIgnoreSpec.from_lines(['**'], pattern)
	return spec


def check_ps_1():
	spec = PathSpec.from_lines('gitignore', ['**'])
	return spec


def check_ps_2():
	pat_type = 'gitignore'
	spec = PathSpec.from_lines(pat_type, ['**'])
	return spec


def check_ps_3():
	spec = PathSpec.from_lines(GitIgnoreBasicPattern, ['**'])
	return spec


def check_ps_4():
	from typing import AnyStr
	def pattern_factory(pattern: AnyStr) -> GitIgnoreBasicPattern:
		return GitIgnoreBasicPattern(pattern)

	spec = PathSpec.from_lines(pattern_factory, ['**'])
	return spec


class LimitedBasicPattern(GitIgnoreBasicPattern):
	@classmethod
	def _audit_segments(cls, segments: tuple[str, ...]) -> None:
		if segments.count('**') > 3:
			raise ValueError('Too many recursive wildcards.')


class LimitedSpecPattern(GitIgnoreSpecPattern):
	@classmethod
	def _audit_segments(cls, segments: tuple[str, ...]) -> None:
		if segments.count('**') > 3:
			raise ValueError('Too many recursive wildcards.')


def check_audited_factories():
	path_spec = PathSpec.from_lines(LimitedBasicPattern, ['src/**'])
	git_spec = GitIgnoreSpec.from_lines(['src/**'], pattern_factory=LimitedSpecPattern)
	return path_spec, git_spec
