
Development Notes
=================

TODO
----

- Document benchmark results:
  - re2 with 150 patterns is 2-3x faster than hyperscan, and 20-30x faster than default.
  - hyperscan with 15 patterns is 35-55% faster than re2, and 1.8-3.8x faster than default.


Python Versions
---------------

These are notes to myself for things to review before decommissioning EoL versions of Python.


### Python

**Python 3.9:**

- Becomes EoL in 2025-10.
- Cannot remove support until RHEL 9 ends support in 2027-05-31.
- Cannot remove support until all major dependents stop supporting Python 3.9.

**Python 3.10:**

- Becomes EoL in 2026-10.

**Python 3.11:**

- Becomes EoL in 2027-10.

**Python 3.12:**

- Becomes EoL in 2028-10.

**Python 3.13:**

- Becomes EoL in 2029-10.

**Python 3.14**

- Becomes EoL in 2030-10.

References:

- [Status of Python Versions](https://devguide.python.org/versions/)


### Linux

Review the following Linux distributions.

**Debian:**

- Goal:
	- Support stable release.
- Debian 12 "Bookworm":
	- Current stable release as of 2025-06-26.
	- Becomes EoL on 2028-06-30.
	- Uses Python 3.11.
- References:
	- [Debian Releases](https://wiki.debian.org/DebianReleases)
	- Package: [python3](https://packages.debian.org/stable/python3)
	- Package: [python3-pathspec](https://packages.debian.org/stable/python3-pathspec)

**Fedora:**

- Goal:
	- Support oldest supported release.
- Fedora 41:
	- Oldest supported release as of 2025-06-26.
	- Becomes EoL on 2025-11-19.
	- Uses Python 3.13.
- References:
	- [End of Life Releases
](https://docs.fedoraproject.org/en-US/releases/eol/)
	- [Fedora Linux 41 Schedule: Key
](https://fedorapeople.org/groups/schedule/f-41/f-41-key-tasks.html)
	- [Multiple Pythons](https://developer.fedoraproject.org/tech/languages/python/multiple-pythons.html)
	- Package: [python-pathspec](https://src.fedoraproject.org/rpms/python-pathspec)

**Gentoo:**

- Uses Python 3.11+ (as of 2025-06-26).
- References:
	- Package: [pathspec](https://packages.gentoo.org/packages/dev-python/pathspec)

**RHEL via Fedora EPEL:**

- Goal:
	- Support oldest release with recent version of *python-pathspec* package.
- RHEL 9:
	- Oldest release with recent version of *python-pathspec* package (v0.12.1/latest from 2023-12-01; as of 2025-06-26).
	- Ends full support on 2027-05-31.
	- Uses Python 3.9.
- References:
	- [Chapter 1. Introduction to Python](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/installing_and_using_dynamic_programming_languages/assembly_introduction-to-python_installing-and-using-dynamic-programming-languages#con_python-versions_assembly_introduction-to-python)
	- Package: [python-pathspec](https://src.fedoraproject.org/rpms/python-pathspec)

**Ubuntu:**

- Goal:
	- Support oldest LTS release in standard support.
- Ubuntu 22.04 "Jammy Jellyfish":
	- Active LTS release as of 2025-06-26.
	- Ends standard support in 2027-04.
	- Package is outdated (v0.9.0 from 2021-07-17; as of 2025-06-26).
	- Uses Python 3.10.
- Ubuntu 24.04 "Noble Numbat":
	- Latest LTS release as of 2025-06-26.
	- Ends standard support in 2029-04.
	- Package is update-to-date (v0.12.1 from 2023-12-10; as of 2025-06-26).
	- Uses Python 3.12.
- References:
	- [Releases](https://wiki.ubuntu.com/Releases)
	- Package: [python3](https://packages.ubuntu.com/jammy/python3) (jammy)
	- Package: [python3](https://packages.ubuntu.com/noble/python3) (noble)
	- Package: [python3-pathspec](https://packages.ubuntu.com/jammy/python3-pathspec) (jammy)
	- Package: [python3-pathspec](https://packages.ubuntu.com/noble/python3-pathspec) (noble)


### PyPI

Review the following PyPI packages.

[ansible-lint](https://pypi.org/project/ansible-lint/)

- v25.9.2 (latest as of 2025-10-20) requires Python 3.10+.
- [ansible-lint on Wheelodex](https://www.wheelodex.org/projects/ansible-lint/).

[black](https://pypi.org/project/black/)

- v25.9.0 (latest as of 2025-10-20) requires Python 3.9+.
- [black on Wheelodex](https://www.wheelodex.org/projects/black/).

[dvc](https://pypi.org/project/dvc/)

- v3.63.0 (latest as of 2025-10-20) requires Python 3.9+.
- [dvc on Wheelodex](https://www.wheelodex.org/projects/dvc/).

[hatchling](https://pypi.org/project/hatchling/)

- v1.27.0 (latest as of 2025-10-20) requires Python 3.8+, but next release will require Python 3.9+.
- [hatchling on Wheelodex](https://www.wheelodex.org/projects/hatchling/).

[yamllint](https://pypi.org/project/yamllint/)

- v1.37.1 (latest as of 2025-10-20) requires Python 3.9+.
- [yamllint on Wheelodex](https://www.wheelodex.org/projects/yamllint/).
