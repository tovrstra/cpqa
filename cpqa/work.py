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


import os, shutil, random

from cpqa import TestInput


__all__ = ['Work']


class Work(object):
    def __init__(self, config):
        self.config = config
        print '... Preparing work tree.'
        # Setup a few directories
        if not os.path.isdir(config.indir):
            raise IOError('Input directory "%s" is not present.' % config.indir)
        if not os.path.isdir(config.refdir):
            os.mkdir(config.refdir)
        if os.path.isdir(config.tstdir):
            raise IOError('Test directory "%s" is already present.' % config.tstdir)
        os.mkdir(config.tstdir)
        # Keep a link to the last test directory.
        if os.path.islink(config.lastlink):
            os.remove(config.lastlink)
        if not os.path.isfile(config.lastlink):
            os.symlink(config.tstdir, config.lastlink)
        # Make a list of all test input files.
        self.test_inputs = []
        for root, dirnames, filenames in os.walk(self.config.indir):
            for fn in filenames:
                if fn.endswith('.inp'):
                    fn = os.path.join(root, fn)
                    prefix = fn[len(self.config.indir)+1:-4]
                    test_input = TestInput(fn, prefix)
                    if test_input.active:
                        self.test_inputs.append(test_input)
        # Translate the dependency strings into dependency test_inputs.
        lookup = dict((test_input.prefix, test_input) for test_input in self.test_inputs)
        for test_input in self.test_inputs:
            test_input.depends = [lookup[depend] for depend in test_input.depends]
            # Just a quick check.
            assert test_input not in test_input.depends
        # Random order
        random.shuffle(self.test_inputs)
