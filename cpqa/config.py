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


import os, imp, datetime, sys, optparse


__all__ = ['Config']


class Config(object):
    def __init__(self, args, use_last=False):
        # Get stuff from the config.py file
        if not os.path.isfile('config.py'):
            raise IOError('Could not find file config.py')
        user_config = imp.load_source('user-config', 'config.py')
        self.cp2k_root = user_config.__dict__.get('cp2k_root', os.path.join('..', 'cp2k'))
        self.arch = user_config.__dict__.get('arch', None)
        self.version = user_config.__dict__.get('version', None)
        self.nproc = user_config.__dict__.get('nproc', 1)
        self.nproc_mpi = user_config.__dict__.get('nproc_mpi', 1)
        self.mpi_prefix = user_config.__dict__.get('mpi_prefix', None)
        os.remove('config.pyc')
        # Some type checking on the config.py data
        if not isinstance(self.cp2k_root, basestring):
            raise TypeError('Error in config.py: cp2k_root must be a string.')
        if not isinstance(self.arch, basestring):
            raise TypeError('Error in config.py: arch must be a string.')
        if not isinstance(self.version, basestring):
            raise TypeError('Error in config.py: version must be a string.')
        if not isinstance(self.nproc, int):
            raise TypeError('Error in config.py: nproc must be an integer.')
        if self.nproc <= 0:
            raise ValueError('Error in config.py: nproc must be strictly positive.')
        if not isinstance(self.nproc_mpi, int):
            raise TypeError('Error in config.py: nproc_mpi must be an integer.')
        if self.nproc_mpi <= 0:
            raise ValueError('Error in config.py: nproc_mpi must be strictly positive.')
        if self.mpi_prefix is not None:
            if not isinstance(self.mpi_prefix, basestring):
                raise TypeError('Error in config.py: mpi_prefix must be a string or None.')
            self.mpi_prefix = self.mpi_prefix % self.nproc_mpi
        # Some derived config vars and checks
        self.cp2k_bin = os.path.join(self.cp2k_root, 'exe', self.arch, 'cp2k.%s' % self.version)
        self.bintag = '%s--%s' % (self.arch, self.version)
        self.lastlink = 'tst--%s--last' % self.bintag
        if use_last:
            # try to find the tst--%s--last link and use that date
            if not os.path.islink(self.lastlink):
                raise RuntimeError('Could not find test output from last run')
            tstdir = os.readlink(self.lastlink)
            self.datetag = tstdir[len(self.bintag)+7:]
        else:
            # define a new date tage
            self.datetag = datetime.datetime.now().strftime('%Y-%m-%d-%a--%H-%M-%S')
        self.runtag = '%s--%s' % (self.bintag, self.datetag)
        self.refdir = 'ref--%s' % self.bintag
        self.tstdir = 'tst--%s' % self.runtag
        self.indir = 'in'
        # Store command line args for test selection
        self.args = args

    def parse_args(self):
        self.select_dirs = []
        self.select_prefixes = []
        self.faster_than = None
        self.slower_than = None
        for arg in self.args:
            if os.path.isfile(arg):
                arg = arg[len(self.indir)+1:-4]
                self.select_prefixes.append(arg)
            elif os.path.isdir(arg):
                arg = arg[len(self.indir)+1:]
                self.select_dirs.append(arg)
            elif arg.startswith('fast:'):
                if self.faster_than is not None or self.slower_than is not None:
                    raise ValueError('Only one fast:x or slow:x argument is allowed.')
                self.faster_than = float(arg[5:])
            elif arg.startswith('slow:'):
                if self.faster_than is not None or self.slower_than is not None:
                    raise ValueError('Only one fast:x or slow:x argument is allowed.')
                self.slower_than = float(arg[5:])
            else:
                raise ValueError('Arguments must be one optional timing restriction, existing directories or input files.')

    def filter_inputs_name(self, test_inputs):
        result = []
        if len(self.select_prefixes) > 0 or len(self.select_dirs) > 0:
            print '... Making selection of inputs (based on names).'
            for test_input in test_inputs:
                done = False
                for select_prefix in self.select_prefixes:
                    if test_input.prefix == select_prefix:
                        result.append(test_input)
                        done = True
                        break
                if done:
                    continue
                for select_dir in self.select_dirs:
                    if test_input.prefix.startswith(select_dir):
                        result.append(test_input)
                        break
        else:
            print '... Taking all input files.'
            result = test_inputs
        return result

    def filter_inputs_timing(self, test_inputs):
        if self.faster_than is None and self.slower_than is None:
            return test_inputs
        elif self.faster_than is not None:
            print '... Selecting fast jobs (faster than %.2fs)' % self.faster_than
            # jobs without timing are not included.
            return [
                ti for ti in test_inputs if
                ti.ref_result is not None and
                ti.ref_result.seconds < self.faster_than
            ]
        else:
            print '... Selecting slow jobs (faster than %.2fs)' % self.slower_than
            # jobs without timing are not included.
            return [
                ti for ti in test_inputs if
                ti.ref_result is not None and
                ti.ref_result.seconds > self.slower_than
            ]
