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


import os, shutil
from optparse import OptionParser

from cpqa.data import TestInput


__all__ = ['import_main']


def import_main(config):
    print '... Importing tests from the CP2K source tree.'

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

    # Remove old test input directory
    if os.path.exists(config.indir):
        shutil.rmtree(config.indir)

    # Load inputs and transform them
    paths_extra = set([])
    for test_dir, test_input, test_index in test_inputs:
        src_test_dir = os.path.join(config.cp2k_root, 'tests', test_dir)
        dst_test_dir = os.path.join(config.indir, test_dir)
        if not os.path.isdir(dst_test_dir):
            os.makedirs(dst_test_dir)
        f_src = file(os.path.join(src_test_dir, test_input), 'r')
        f_dst = file(os.path.join(dst_test_dir, test_input), 'w')
        if not is_converted(f_src):
            # Mark converted inputs.
            print >> f_dst, '#CPQA CONVERTED'
            # More serious directives
            if test_index >= 0:
                regex, column = test_types[test_index].split('!')
                # escape _some_ special characters that are to be taken literally
                regex = regex.replace('|', '\|').replace('(', '\(').replace(')', '\)')
                regex = regex.replace('+', '\+')
                print >> f_dst, '#CPQA TEST SCALAR \'%s\' %i' % (
                   regex, int(column) - 1
                )
            resets = reset_info.get(os.path.join(test_dir, test_input), [])
            for reset in resets:
                print >> f_dst, '#CPQA RESET', reset[0]
                for line in reset[1:]:
                    print >> f_dst, '#          ', line
        # Copy of the actual test input
        for line in f_src:
            print >> f_dst, line[:-1]
        f_src.close()
        f_dst.close()
        # Get the extra paths
        test_input = TestInput(os.path.join(config.cp2k_root, 'tests'), os.path.join(test_dir, test_input))
        for path_extra in test_input.paths_extra:
            paths_extra.add(path_extra)

    # Copy extra files needed by the inputs
    for path_extra in paths_extra:
        extra_dir = os.path.dirname(path_extra)
        src_path_extra = os.path.join(config.cp2k_root, 'tests', path_extra)
        dst_path_extra = os.path.join(config.indir, path_extra)
        dst_extra_dir = os.path.join(config.indir, extra_dir)
        if not os.path.isdir(dst_extra_dir):
            os.makedirs(dst_extra_dir)
        if os.path.isfile(src_path_extra):
            shutil.copy(src_path_extra, dst_extra_dir)
        else:
            shutil.copytree(src_path_extra, dst_path_extra)


def is_converted(f):
    result = False
    for line in f:
        if line.strip() == '#CPQA CONVERTED':
            result = True
            break
    f.seek(0)
    return result
