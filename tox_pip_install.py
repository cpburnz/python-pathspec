#!/usr/bin/env python
# This file is part of packagename <https://github.com/kevinoid/packagename>
# Made available under CC0 1.0 Universal, see LICENSE.txt
# Copyright 2019-2020 Kevin Locke <kevin@kevinlocke.name>
"""
Script to reinstall pip before running `pip install`.

Workaround for https://bugs.debian.org/962654
"""

import os
import sys

# Must be invoked with pip package (optionally version-constrained) as first
# argument, install options+packages as subsequent options.
if len(sys.argv) < 3 or not sys.argv[1].startswith('pip'):
    sys.stderr.write(
        'Usage: ' + sys.argv[0] + ' <pip version> [options] <packages...>\n'
    )
    sys.exit(1)

# Workaround is only needed on Debian (and derivatives)
if os.path.exists('/etc/debian_version'):
    pip_exit_code = os.spawnl(
        os.P_WAIT,
        sys.executable,
        sys.executable,
        '-m',
        'pip',
        'install',
        '--force-reinstall',
        '--no-compile',
        sys.argv[1],
    )
    if pip_exit_code != 0:
        sys.exit(pip_exit_code)

os.execv(
    sys.executable, [sys.executable, '-m', 'pip', 'install'] + sys.argv[2:]
)
