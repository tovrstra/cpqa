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


from cpqa import Config, compile_cp2k, Work, Runner, log_txt, log_html, Timer

import os, sys


def main():
    # Measure the total wall-time
    timer = Timer()
    # Load the configuration (from config.py file and from command line args).
    config = Config()
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
