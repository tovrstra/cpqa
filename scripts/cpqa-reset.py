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


import os, sys, tempfile, cPickle
from optparse import OptionParser

from cpqa import Config, LastWork


usage = """Usage: %prog [options] [input1.inp input2.inp ...] [directory1 directory2 ...]

Resets tests that failed during the last test run.

A motivation of the reset can be provided with the -m option, otherwise an
editor is fired up to write a motivation. Without motivation, the reset script
aborts.

By default all tests that have a different output than the reference, but have
no other issues, are considered for the resest. One may restrict this list
furhter by specifying inputs and/or directories at the command line.

Before the actual reset, a list is shown with all tests that will be reset and
one must confirm before the script proceeds.
"""


def parse_args():
    parser = OptionParser(usage)
    parser.add_option(
        '--motivation', '-m',
        help="Provide a motivation for the reset. If not given a motivation "
        "can be entered in an editor.",
    )
    (options, args) = parser.parse_args()
    return options, args



def get_editor():
    editor = os.getenv('EDITOR')
    if editor is None:
        editor = 'vi'
    return editor


def get_motivation(options):
    if options.motivation is not None:
        motivation = options.motivation
    else:
        fn_tmp = tempfile.mktemp('cpqa')
        editor = get_editor()
        os.system('%s %s' % (editor, fn_tmp))
        if os.path.isfile(fn_tmp):
            f = open(fn_tmp)
            motivation = f.read()
            f.close()
            os.remove(fn_tmp)
        else:
            motivation = ''

    motivation = motivation.strip()
    if len(motivation) == 0:
        print 'No motivation provided. Aborting.'
        sys.exit(1)
    return motivation


def get_different(config):
    print config.tstdir
    # Get the test inputs
    last_work = LastWork(config)
    test_inputs = config.filter_inputs_name(last_work.test_inputs)
    # Select those tests where the comparison with the reference number failed,
    # but that showed no other problems.
    different = []
    for test_input in test_inputs:
        fn = os.path.join(config.tstdir, test_input.prefix + '.pp')
        if os.path.isfile(fn):
            f = file(fn)
            tst_result = cPickle.load(f)
            f.close()
            if not tst_result.flags['different']:
                continue
            del tst_result.flags['different']
            del tst_result.flags['verbose']
            if any(tst_result.flags.itervalues()):
                continue
            different.append(test_input)
    return different


def get_confirmation(different):
    print
    print 'The following tests will be reset:'
    for ti in different:
        print ti.prefix
    answer = raw_input('Do you want to proceed? [y/N]: ')
    return answer.lower() == 'y'


def do_reset(config, motivation, different):
    # Split the motivation into lines and add comment characters
    motivation = ['# ' + l for l in motivation.split('\n')]
    # We have to figure out which TEST_FILES_RESET files in the CP2K input need
    # to be modified, and which lines should be added to each file.
    todo = {}
    for ti in different:
        dirname = os.path.dirname(ti.prefix)
        inpname = os.path.basename(ti.prefix) + '.inp'
        reset_file = os.path.join(config.cp2k_root, 'tests', dirname, 'TEST_FILES_RESET')
        l = todo.setdefault(reset_file, motivation)
        l.append(inpname)
    # Modify the files
    for fn, lines in todo.iteritems():
        f = open(fn, 'a')
        for line in lines:
            print >> f, line
        f.close()
    # Give some useful feedback
    print
    print '.. The appropriate TEST_FILES_RESET files were modified.'
    print 'During the next test run (cpqa-main.py with default import),',
    print 'the reference data of these tests will be reset.'


def main():
    options, args = parse_args()
    # Load the configuration (from config.py file and from command line args).
    config = Config(args, use_last=True)
    # Get the list of failed tests during the last run
    different = get_different(config)
    # Get the confirmation that this needs to be done.
    if not get_confirmation(different):
        sys.exit(1)
    # Request the motivation
    motivation = get_motivation(options)
    # Apply the reset
    do_reset(config, motivation, different)

if __name__ == '__main__':
    # Only run main when this script is executed as a program, i.e. not imported
    # as a module.
    main()
