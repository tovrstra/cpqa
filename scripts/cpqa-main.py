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


import os, sys
from optparse import OptionParser

from cpqa import Config, compile_cp2k, Work, Runner, log_txt, log_html, Timer, \
    import_main


usage = """Usage: %prog [options] [input1.inp input2.inp ...] [directory1 directory2 ...] [fast:n|slow:n]

The order of the command line arguments does not matter. If no arguments are
given, all tests are executed.

This is the workhorse of CPQA. It runs all the tests and in case some tests
fail or give wrong results, it makes an overview of the failures in text and
html format.
"""


def parse_args():
    parser = OptionParser(usage)
    parser.add_option(
        "--no-import", default=True, action='store_false', dest='do_import',
        help="Do not import tests from the cp2k source tree",
    )
    (options, args) = parser.parse_args()
    return options, args


def main():
    options, args = parse_args()
    # Measure the total wall-time
    timer = Timer()
    # Load the configuration (from config.py file).
    config = Config(args)
    # Optionally import tests from the source tree.
    if options.do_import:
        import_main(config)
    # Parse the command line after the import to check the presence of the
    # selected inputs
    config.parse_args()
    # Initialize the working directory.
    work = Work(config)
    # Try to compile CP2K
    compile_cp2k(config)
    # Create a test runner. It will produce a Makefile based on the #CPQA
    # directives in the test inputs. It runs the make file, logs some screen
    # output and collects all the test results in the attributes of the runner
    # object.
    runner = Runner(work)
    # Stop timer
    timer.stop()
    # Print a summary on screen
    log_txt(runner, timer, sys.stdout)
    # Create a text log file
    log_txt(runner, timer)
    # Create a html log file
    log_html(runner, timer)


if __name__ == '__main__':
    # Only run main when this script is executed as a program, i.e. not imported
    # as a module.
    main()
