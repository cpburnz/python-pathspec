
Development Notes
=================

Python Versions
---------------

These are notes to myself for things to review before decommissioning EoL versions of Python.


### Python

**Python 3.7:**

- EoL as of 2023-06-27.

**Python 3.8:**

- Becomes EoL in 2024-10.

References:

- [Status of Python Versions](https://devguide.python.org/versions/)


### Linux

Review the following Linux distributions.

**CentOS:**

- TODO

**Debian:**

- Goal:
	- Support stable release.
- Debian 12 "Bookworm":
	- Current stable release as of 2023-09-06.
	- EoL date TBD.
	- Uses Python 3.11.
- References:
	- [Debian Releases](https://wiki.debian.org/DebianReleases)
	- Package: [python3](https://packages.debian.org/stable/python3)
	- Package: [python3-pathspec](https://packages.debian.org/stable/python3-pathspec)

**Fedora:**

- Goal:
	- Support oldest supported release.
- Fedora 37:
	- Oldest supported release as of 2023-09-06.
	- Becomes EoL on 2023-11-14.
	- Uses Python 3.11.
- References:
	- [End of Life Releases
](https://docs.fedoraproject.org/en-US/releases/eol/)
	- [Fedora Linux 39 Schedule: Key
](https://fedorapeople.org/groups/schedule/f-39/f-39-key-tasks.html)
	- [Python](https://docs.fedoraproject.org/en-US/fedora/f37/release-notes/developers/Development_Python/)
	- Package: [python-pathspec](https://src.fedoraproject.org/rpms/python-pathspec)

**Gentoo:**

- Uses Python 3.10+.
- References:
	- Package: [pathspec](https://packages.gentoo.org/packages/dev-python/pathspec)

**RHEL via Fedora EPEL:**

- Goal:
	- Support oldest release with recent version of *python-pathspec* package.
- RHEL 9:
	- Oldest release with recent version of *python-pathspec* package (v0.10.1 from 2022-09-02; as of 2023-09-07).
	- Ends full support on 2027-05-31.
	- Uses Python 3.9.
- References:
	- [Chapter 1. Introduction to Python](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/installing_and_using_dynamic_programming_languages/assembly_introduction-to-python_installing-and-using-dynamic-programming-languages#con_python-versions_assembly_introduction-to-python)
	- Package: [python-pathspec](https://src.fedoraproject.org/rpms/python-pathspec)

**Ubuntu:**

- Goal:
	- Support oldest LTS release in standard support.
- Ubuntu 20.04 "Focal Fossa":
	- Oldest LTS release in standard support as of 2023-09-06.
	- Ends standard support in 2025-04.
	- Package is outdated (v0.7.0 from 2019-12-27; as of 2023-09-06).
	- Uses Python 3.8.
- Ubuntu 22.04 "Jammy Jellyfish":
	- Latest LTS release as of 2023-09-06.
	- Ends standard support in 2027-04.
	- Package is outdated (v0.9.0 from 2021-07-17; as of 2023-09-06).
	- Uses Python 3.10.
- References:
	- [Releases](https://wiki.ubuntu.com/Releases)
	- Package: [python3](https://packages.ubuntu.com/focal/python3) (focal)
	- Package: [python3](https://packages.ubuntu.com/jammy/python3) (jammy)
	- Package: [python3-pathspec](https://packages.ubuntu.com/focal/python3-pathspec) (focal)
	- Package: [python3-pathspec](https://packages.ubuntu.com/jammy/python3-pathspec) (jammy)


### PyPI

Review the following PyPI packages.

[ansible-lint](https://pypi.org/project/ansible-lint/)

- v6.19.0 (latest as of 2023-09-06) requires Python 3.9+.
- [ansible-lint on Wheelodex](https://www.wheelodex.org/projects/ansible-lint/).

[black](https://pypi.org/project/black/)

- v23.7.0 (latest as of 2023-09-06) requires Python 3.8+.
- [black on Wheelodex](https://www.wheelodex.org/projects/black/).

[dvc](https://github.com/iterative/dvc)

- v3.23.0 (latest as of 2023-09-30) requires Python 3.8+.
- [dvc on Wheelodex](https://www.wheelodex.org/projects/dvc/).

[hatchling](https://pypi.org/project/hatchling/)

- v1.18.0 (latest as of 2023-09-06) requires Python 3.8+.
- [hatchling on Wheelodex](https://www.wheelodex.org/projects/hatchling/).

[yamllint](https://pypi.org/project/yamllint/)

- v1.33.0 (latest as of 2023-12-09) requires Python 3.8+.
- [yamllint on Wheelodex](https://www.wheelodex.org/projects/yamllint/).
