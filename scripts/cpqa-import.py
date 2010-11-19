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

from cpqa import Config, TestInput


def main():
    # Load the configuration (from config.py file).
    config = Config()

    # load list of test types
    test_types= []
    f = open(os.path.join(config.cp2k_root, 'tests', 'TEST_TYPES'))
    f.next() # skip first line
    for line in f:
        line = line[:line.find('#')].strip()
        if len(line) == 0:
            continue
        test_types.append(line)
    f.close()

    # Load all test dirs
    test_dirs = []
    f = open(os.path.join(config.cp2k_root, 'tests', 'TEST_DIRS'))
    for line in f:
        if line.startswith('#'):
            continue
        test_dirs.append(line.strip())
    f.close()

    # Load all test inputs
    test_inputs = []
    for test_dir in test_dirs:
        f = open(os.path.join(config.cp2k_root, 'tests', test_dir, 'TEST_FILES'))
        for line in f:
            if line.startswith('#'):
                continue
            test_input, test_index = line.split()
            test_index = int(test_index)-1
            test_inputs.append((test_dir, test_input, test_index))
        f.close()

    # Load reset information
    reset_info = {}
    for test_dir in test_dirs:
        f = open(os.path.join(config.cp2k_root, 'tests', test_dir, 'TEST_FILES_RESET'))
        # skip the first two lines.
        try:
            f.next()
            f.next()
        except StopIteration:
            pass
        new_comments = False
        comments = []
        for line in f:
            if line.startswith('#'):
                if new_comments:
                    comments = []
                line = line[1:].strip()
                if len(line) > 0:
                    comments.append(line)
                new_comments = False
            else:
                if not new_comments:
                    if len(comments) == 0:
                        comments = ['']
                    comments = tuple(comments)
                    new_comments = True
                line = line.strip()
                l = reset_info.setdefault(os.path.join(test_dir, line), [])
                l.append(comments)
        f.close()

    # Load inputs and transform them
    extra_paths = set([])
    for test_dir, test_input, test_index in test_inputs:
        if test_input.endswith('.restart'):
            print test_input
            continue
        src_test_dir = os.path.join(config.cp2k_root, 'tests', test_dir)
        dst_test_dir = os.path.join(config.indir, test_dir)
        if not os.path.isdir(dst_test_dir):
            os.makedirs(dst_test_dir)
        f_src = file(os.path.join(src_test_dir, test_input), 'r')
        f_dst = file(os.path.join(dst_test_dir, test_input), 'w')
        # Just something to make sure the test gets picked up.
        # TODO: only do these if there are no other CPQA flags.
        print >> f_dst, '#CPQA FOO'
        # More serious directives
        if test_index >= 0:
            regex, column = test_types[test_index].split('!')
            print >> f_dst, '#CPQA TEST SINGLE-VALUE \'%s\' %i' % (
               regex.replace('|', '\|'), int(column) - 1
            )
        resets = reset_info.get(os.path.join(test_dir, test_input), [])
        for reset in resets:
            print >> f_dst, '#CPQA RESET', reset[0]
            for line in reset[1:]:
                print >> f_dst, '#          ', line
        # Copy of the actual test input
        for line in f_src:
            print >> f_dst, line[:-1]
            #if len(words) == 2 and 'FILE' in words[0] and 'FORMAT' not in words[0] and \
            #   not os.path.exists(os.path.join(src_test_dir, words[1])) and not '__STD_OUT__' in words[1]:
            #    dep_path = os.path.join(test_dir, words[1])
            #    dep_path = os.path.normpath(dep_path)
            #    print os.path.join(test_dir, test_input),
            #    print words[0],
            #    print dep_path
        f_src.close()
        f_dst.close()
        # Get the extra paths
        fn = os.path.join(src_test_dir, test_input)
        prefix = os.path.join(test_dir, test_input)[:-4]
        test_input = TestInput(fn, prefix)
        for extra_path in test_input.extra_paths:
            extra_paths.add(extra_path)

    # Copy extra files needed by the inputs
    for extra_path in extra_paths:
        extra_dir = os.path.dirname(extra_path)
        src_extra_path = os.path.join(config.cp2k_root, 'tests', extra_path)
        dst_extra_path = os.path.join(config.indir, extra_path)
        dst_extra_dir = os.path.join(config.indir, extra_dir)
        if not os.path.isdir(dst_extra_dir):
            os.makedirs(dst_extra_dir)
        if os.path.isfile(src_extra_path):
            shutil.copy(src_extra_path, dst_extra_dir)
        else:
            shutil.copytree(src_extra_path, dst_extra_path)

if __name__ == '__main__':
    # Only run main when this script is executed as a program, i.e. not imported
    # as a module.
    main()
