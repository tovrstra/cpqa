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
    def __init__(self, fn, prefix):
        self.fn = fn
        self.prefix = prefix
        self.active = False
        self.num_resets = 0
        self.tests = []
        self.depends = []
        self.extra_paths = []
        f = open(fn)
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
                    line = line[8:].strip()
                    self.depends.append(os.path.join(os.path.dirname(prefix), line[:-4]))
            else:
                words = line.split()
                if len(words) == 2 and len(words[1]) > 1 and words[1] != '..':
                    extra_input = words[1]
                    if (extra_input[0] == '"' and extra_input[-1] == '"') or \
                       (extra_input[0] == "'" and extra_input[-1] == "'"):
                        extra_input = extra_input[1:-1]
                    dirname = os.path.dirname(fn)
                    if os.path.isfile(os.path.join(dirname, extra_input)):
                        # Make sure none of the data has any traces of the 'in',
                        # 'ref-*' or 'tst-*' directory.
                        dirname = os.path.dirname(prefix)
                        extra_path = os.path.join(dirname, extra_input)
                        extra_path = os.path.normpath(extra_path)
                        self.extra_paths.append(extra_path)
        f.close()
        for test in self.tests:
            for extra_input in test.extra_inputs:
                dirname = os.path.dirname(prefix)
                extra_path = os.path.join(dirname, extra_input)
                extra_path = os.path.normpath(extra_path)
                self.extra_paths.append(extra_path)


class TestResult(object):
    def __init__(self, prefix, flags, seconds_cp2k, seconds, tests, messages,
                 last_out_lines, last_o_lines, last_e_lines):
        self.prefix = prefix
        self.flags = flags
        self.seconds_cp2k = seconds_cp2k
        self.seconds = seconds
        self.tests = tests
        self.messages = messages
        self.last_out_lines = last_out_lines
        self.last_o_lines = last_o_lines
        self.last_e_lines = last_e_lines
        # derived
        self.seconds_script = seconds - seconds_cp2k
