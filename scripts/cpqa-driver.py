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


import sys, os, shutil, datetime, cPickle, traceback

from cpqa import TestInput, TestResult, harvest_test, Timer, tail


def parse_args():
    args = sys.argv[1:]
    if len(args) == 3:
        cp2k_bin, tstpath, refdir = args
        mpi_prefix = ''
    elif len(args) == 4:
        cp2k_bin, tstpath, refdir, mpi_prefix = args
    else:
        raise TypeError('Excpecting three or four arguments.')
    if not os.path.isfile(cp2k_bin):
        raise ValueError('CP2K binary "%s" not found.' % args[0])
    return cp2k_bin, tstpath, refdir, mpi_prefix


def print_log_line(tstpath, flags, sec_cp2k, sec_all):
    print "CPQA-PREFIX",
    tag = ''
    for key, value in sorted(flags.iteritems()):
        if value:
            tag += key[0].upper()
        else:
            tag += "-"
    print tag,
    print '%6.2f' % sec_cp2k,
    print '%6.2f' % (sec_all-sec_cp2k),
    print tstpath


def main():
    timer_all = Timer()
    # Get command line arguments
    cp2k_bin, tstpath, refdir, mpi_prefix = parse_args()
    # Flags to display the status of the test.
    flags = {}
    # To record error messages of this script:
    messages = []
    # Run cp2k
    tstdir, prefix = os.path.split(tstpath)
    command = 'cd ./%s; %s %s -i %s.inp -o %s.out > %s.o 2> %s.e' % (tstdir,
        mpi_prefix, cp2k_bin, prefix, prefix, prefix, prefix)
    timer_cp2k = Timer()
    retcode = os.system(command)
    timer_cp2k.stop()
    flags['failed'] = (retcode != 0)
    # Get the last 20 lines
    last_out_lines = tail(os.path.join(tstdir, prefix + '.out'))
    last_o_lines = tail(os.path.join(tstdir, prefix + '.o'))
    last_e_lines = tail(os.path.join(tstdir, prefix + '.e'))
    flags['verbose'] = len(last_e_lines) > 0 or len(last_o_lines) > 0
    # Check on refdir
    refdir = os.path.join('..', refdir, tstdir)
    refpath = os.path.join(refdir, prefix)
    flags['new'] = not os.path.isfile(refpath + '.pp')
    # Extract the tests and count the number of resets
    test_input_tst = TestInput(tstpath + '.inp', tstpath)
    num_resets_tst = test_input_tst.num_resets
    tests = test_input_tst.tests
    if flags['new']:
        num_resets_ref = num_resets_tst
    else:
        test_input_ref = TestInput(refpath + '.inp', tstpath)
        num_resets_ref = test_input_ref.num_resets
    flags['reset'] = (num_resets_tst > num_resets_ref)
    flags['error'] = False
    if num_resets_tst < num_resets_ref:
        flags['error'] = True
        messages.append('Error: The number of reset directives decreased.')
    # Collect fragments from output for tests.
    flags['missing'] = False
    harvest_test(tstpath, refpath, tests, flags['new'], messages)
    # Do the actual tests.
    flags['wrong'] = False
    flags['different'] = False
    for test in tests:
        if not test.complete(flags['new']):
            flags['missing'] = True
        else:
            try:
                test.run(flags['new'])
            except Exception:
                messages.append(traceback.format_exc())
            if test.wrong is True:
                flags['wrong'] = True
            if test.different is True:
                flags['different'] = True
    # Determine error flag
    flags['error'] = len(messages) > 0
    # Determine the OK flag
    flags['ok'] = not (flags['wrong'] or (flags['different'] and not
                  flags['reset']) or flags['missing'] or flags['failed'] or
                  flags['error'])
    # Write the TestResult to a pickle file
    timer_all.stop()
    test_result = TestResult(prefix, flags, timer_cp2k.seconds,
        timer_all.seconds, tests, messages, last_out_lines, last_o_lines,
        last_e_lines)
    f = open(tstpath + '.pp', 'w')
    cPickle.dump(test_result, f, -1)
    f.close()
    # Copy the tests to the reference directory if needed.
    if (flags['new'] or flags['reset']) and flags['ok']:
        if not os.path.isdir(refdir):
            os.makedirs(refdir)
        for suffix in '.inp', '.out', '.pp':
            shutil.copy(tstpath + suffix, refpath + suffix)
    # Print some screen output.
    print_log_line(tstpath, flags, timer_cp2k.seconds, timer_all.seconds)



if __name__ == '__main__':
    # Only run main when this script is executed as a program, i.e. not imported
    # as a module.
    main()
