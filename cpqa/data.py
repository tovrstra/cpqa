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


import os, shlex

from cpqa.tests import test_factories


__all__ = ['TestInput', 'TestResult']


class TestInput(object):
    def __init__(self, root, path_inp):
        '''
           *Arguments:*

           root
                The root directory in which the test resides.

           path_inp
                The path to the test input relative to the root directory.
        '''
        self.root = root
        self.path_inp = path_inp
        self.active = False
        self.num_resets = 0
        self.tests = []
        self.depends = []
        self.paths_extra = []
        # related to input path
        if path_inp.endswith('.inp'):
            pre = path_inp[:-4]
        elif path_inp.endswith('.restart'):
            pre = path_inp[:-8]
        else:
            pre = path_inp
        self.path_pp = pre + '.pp'
        self.path_out = pre + '.out'
        self.path_stdout = pre + '.stdout'
        self.path_stderr = pre + '.stderr'

        dirname = os.path.join(os.path.dirname(path_inp))
        f = open(os.path.join(root, path_inp))
        for line in f:
            if line.startswith('#CPQA '):
                line = line[6:].strip()
                self.active = True
                if line.startswith('RESET'):
                    self.num_resets += 1
                elif line.startswith('TEST '):
                    line = line[5:]
                    words = shlex.split(line)
                    key = words[0].lower()
                    self.tests.append(test_factories[key](words[1:]))
                elif line.startswith('DEPENDS '):
                    fn_depends = line[8:].strip()
                    path_depends = os.path.join(dirname, fn_depends)
                    path_depends = os.path.normpath(path_depends)
                    self.depends.append(path_depends)
                elif line.startswith('INCLUDE '):
                    fn_extra = line[8:].strip()
                    path_extra = os.path.join(dirname, fn_extra)
                    path_extra = os.path.normpath(path_extra)
                    self.paths_extra.append(path_extra)
            else:
                words = line.split()
                for fn_extra in words[1:]:
                    if len(fn_extra) <= 1:
                        continue
                    if fn_extra == '..':
                        continue
                    if (fn_extra[0] == '"' and fn_extra[-1] == '"') or \
                       (fn_extra[0] == "'" and fn_extra[-1] == "'"):
                        fn_extra = fn_extra[1:-1]
                    if os.path.isfile(os.path.join(root, dirname, fn_extra)):
                        # Make sure none of the data has any traces of the 'in',
                        # 'ref-*' or 'tst-*' directory.
                        path_extra = os.path.join(dirname, fn_extra)
                        path_extra = os.path.normpath(path_extra)
                        self.paths_extra.append(path_extra)

        f.close()
        for test in self.tests:
            for fn_extra in test.fns_extra:
                path_extra = os.path.join(dirname, fn_extra)
                path_extra = os.path.normpath(path_extra)
                self.paths_extra.append(path_extra)


class TestResult(object):
    def __init__(self, path_inp, flags, seconds_bin, seconds, tests,
                 messages, last_out_lines, last_stdout_lines, last_stderr_lines):
        self.path_inp = path_inp
        self.flags = flags
        self.seconds_bin = seconds_bin
        self.seconds = seconds
        self.tests = tests
        self.messages = messages
        self.last_out_lines = last_out_lines
        self.last_stdout_lines = last_stdout_lines
        self.last_stderr_lines = last_stderr_lines
        # derived
        self.seconds_script = seconds - seconds_bin
