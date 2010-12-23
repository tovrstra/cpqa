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

from cpqa.data import TestInput


__all__ = ['Work', 'LastWork']


def is_binary(filename):
    """Return true if the given filename is binary."""
    f = open(filename, 'rb')
    try:
        while 1:
            chunk = f.read(1024)
            if '\0' in chunk: # found null byte
                return True
            if len(chunk) < 1024:
                break # done
    finally:
        f.close()
    return False


def find_inputs(indir):
    test_inputs = []
    for root, dirnames, filenames in os.walk(indir):
        for fn_inp in filenames:
            if not (fn_inp.endswith('.inp') or fn_inp.endswith('.restart')):
                continue
            path_inp = os.path.join(root[len(indir)+1:], fn_inp)
            if is_binary(os.path.join(indir, path_inp)):
                continue
            test_input = TestInput(indir, path_inp)
            if not test_input.active:
                continue
            test_inputs.append(test_input)
    return test_inputs


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
        self.test_inputs = find_inputs(config.indir)
        # Translate the dependency strings into dependency test_inputs.
        lookup = dict((test_input.path_inp, test_input) for test_input in self.test_inputs)
        for test_input in self.test_inputs:
            test_input.depends = [lookup[depend] for depend in test_input.depends]
            # Just a quick check.
            assert test_input not in test_input.depends
        # Random order
        random.shuffle(self.test_inputs)


class LastWork(object):
    def __init__(self, config):
        self.config = config
        print '... Checking work tree.'
        # Setup a few directories
        if not os.path.isdir(config.indir):
            raise IOError('Input directory "%s" is not present.' % config.indir)
        if not os.path.isdir(config.tstdir):
            raise IOError('Test directory "%s" is not present.' % config.tstdir)
        # Make a list of all test input files.
        self.test_inputs = find_inputs(config.tstdir)
