# Security Policy

## Reporting a Vulnerability

Contact information is available on PyPI.

## Scope

The following are not considered vulnerabilities in pathspec:

- *ReDoS / regular expression complexity*: pathspec is a pattern-matching library, not a sandboxed input parser.
  The regex complexity is proportional to that of the pattern.
  Applications that expose pattern input to untrusted users are responsible for sanitizing that input.

- Any actual vulnerabilities discovered in Python's re module, hyperscan, or google-re2 should be reported to the maintainers of those libraries.
