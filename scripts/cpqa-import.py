#!/usr/bin/env python
# CPQA is a Quality Assurance framework for CP2K.
# Copyright (C) 2010 Toon Verstraelen <Toon.Verstraelen@UGent.be>.
#
# This file is part of CPQA.
#
# CPQA is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# CPQA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
'''Program to convert the legacy CP2K tests to the CPQA format'''


import os, shutil
from optparse import OptionParser

from cpqa import Config, import_main


usage = """Usage: %prog

No arguments are allowed.

This script imports the test files from the cp2k source tree and adds CPQA tags
to the inputs based on the legacy test directory layout. All input files and
related files are stored in a subdirectory 'in' of the current corking
directory. This is the location where the cpqa-main.py script will look for
test inputs.
"""


def parse_args():
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args) > 0:
        raise TypeError('Expecting no command line arguments.')


def main():
    parse_args()
    config = Config([])
    import_main(config)


if __name__ == '__main__':
    # Only run main when this script is executed as a program, i.e. not imported
    # as a module.
    main()
