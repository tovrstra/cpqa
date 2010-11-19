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


import os, subprocess, shutil, cPickle

from cpqa.shell import du


__all__ = ['Runner']


class Runner(object):
    def __init__(self, work):
        self.work = work
        self.config = work.config
        self._test_inputs = []
        self.select_name()
        self.select_timing()
        self.select_dependencies()
        self.sort_test_inputs()
        self.copy_inputs()
        self.create_makefile()
        self.run_makefile()
        self.collect_test_results()
        self.get_disk_usage()

    def _add_test_input(self, test_input):
        # Try to get the reference results.
        fn = os.path.join(self.config.refdir, test_input.prefix + '.pp')
        if os.path.isfile(fn):
            f = file(fn)
            test_input.ref_result = cPickle.load(f)
            f.close()
        else:
            test_input.ref_result = None
        self._test_inputs.append(test_input)

    def select_name(self):
        # Make a selection of test input files.
        if len(self.config.select_prefixes) > 0 or len(self.config.select_dirs) > 0:
            print '... Making selection of inputs (based on names).'
            for test_input in self.work.test_inputs:
                done = False
                for select_prefix in self.config.select_prefixes:
                    if test_input.prefix == select_prefix:
                        self._add_test_input(test_input)
                        done = True
                        break
                if done:
                    continue
                for select_dir in self.config.select_dirs:
                    if test_input.prefix.startswith(select_dir):
                        self._add_test_input(test_input)
                        break
        else:
            print '... Taking all input files.'
            for test_input in self.work.test_inputs:
                self._add_test_input(test_input)

    def select_timing(self):
        if self.config.faster_than is None and self.config.slower_than is None:
            return
        if self.config.faster_than is not None:
            print '... Selecting fast jobs (faster than %.2fs)' % self.config.faster_than
            # jobs without timing are not included.
            self._test_inputs = [
                ti for ti in self._test_inputs if
                ti.ref_result is not None and
                ti.ref_result.seconds < self.config.faster_than
            ]
        if self.config.slower_than is not None:
            print '... Selecting slow jobs (faster than %.2fs)' % self.config.slower_than
            # jobs without timing are not included.
            self._test_inputs = [
                ti for ti in self._test_inputs if
                ti.ref_result is not None and
                ti.ref_result.seconds > self.config.slower_than
            ]

    def _with_dependencies(self, original):
        with_deps = set([])
        unchecked = set(original)
        while len(unchecked) > 0:
            tocheck = unchecked.pop()
            # Add all dependencies to the unchecked set, unless they are already
            # in with_deps.
            for depend in tocheck.depends:
                if depend not in with_deps:
                    unchecked.add(depend)
            # Add the checked test input to current
            with_deps.add(tocheck)
        return with_deps

    def select_dependencies(self):
        print '... Adding dependency tests.'
        # Add the input files to the list that are needed for the selection.
        # In principle the make program can take care of this, but we'd like to
        # know which jobs are going to be executed. Then we can copy only the
        # input files needed for this run, and we can give decent progress info.
        # It also gives us the opportunity to sort the jobs from slow to fast.
        original = set(self._test_inputs)
        extra = self._with_dependencies(original) - original
        for test_input in extra:
            self._add_test_input(test_input)
        print '... Total number of jobs: %i' % len(self._test_inputs)

    def sort_test_inputs(self):
        # First compute the timing including the dependencies.
        for test_input in self._test_inputs:
            # Collect all direct and indirect dependencies and the job itself.
            with_deps = self._with_dependencies([test_input])
            sort_key = 0.0
            for tmp in with_deps:
                if tmp.ref_result is None:
                    sort_key = None
                    break
                else:
                    sort_key += tmp.ref_result.seconds
            test_input.sort_key = sort_key
        # Sort based on these timings.
        def compare(ti1, ti2):
            if ti1.sort_key is None and ti2.sort_key is None:
                return 0
            elif ti1.sort_key is None:
                return +1
            elif ti2.sort_key is None:
                return -1
            else:
                return cmp(ti1.sort_key, ti2.sort_key)
        self._test_inputs.sort(compare, reverse=True)

    def copy_inputs(self):
        print '... copying inputs and related files.'
        # Copy only the input files needed to run this batch of tests.
        # - Fist make a complete list of paths, including the extra_inputs
        all_paths = set([])
        for test_input in self._test_inputs:
            all_paths.add(test_input.prefix + '.inp')
            for extra_path in test_input.extra_paths:
                all_paths.add(extra_path)
        # - Then copy the stuff
        for path in all_paths:
            dirname = os.path.dirname(path)
            src_path = os.path.join(self.config.indir, path)
            dst_dir = os.path.join(self.config.tstdir, dirname)
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)
            shutil.copy(src_path, dst_dir)

    def create_makefile(self):
        # Write the Makefile.
        print '... Creating makefile for test jobs.'
        f = file(os.path.join(self.config.tstdir, 'Makefile'), 'w')
        print >> f, 'all: %s' % (' '.join(test_input.prefix + '.out' for test_input in self._test_inputs))
        for test_input in self._test_inputs:
            print >> f, '%s: %s' % (
                test_input.prefix + '.out',
                ' '.join(depend.prefix + '.out' for depend in test_input.depends)
            )
            if self.config.mpi_prefix is None:
                print >> f, '\tcpqa-driver.py %s %s %s' % (
                    os.path.abspath(self.config.cp2k_bin),
                    test_input.prefix, self.config.refdir
                )
            else:
                print >> f, '\tcpqa-driver.py %s %s %s \'%s\'' % (
                    os.path.abspath(self.config.cp2k_bin),
                    test_input.prefix, self.config.refdir,
                    self.config.mpi_prefix
                )
            print >> f
        f.close()

    def run_makefile(self):
        print '... Running test jobs.'
        if self.config.mpi_prefix is None:
            nproc_make = self.config.nproc
        else:
            nproc_make = self.config.nproc/self.config.nproc_mpi
        args = ['make', '-j', str(nproc_make)]
        print '~~~~ ~~~~~~~~~ ~~~~~~ ~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        print 'Prog   Flags    CP2K  Script Test prefix'
        print '~~~~ ~~~~~~~~~ ~~~~~~ ~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        p = subprocess.Popen(args, 1, stdout=subprocess.PIPE, cwd=self.config.tstdir)
        total = len(self._test_inputs)
        counter = 0
        while True:
            line = p.stdout.readline()
            if len(line) == 0: break
            if line.startswith('CPQA-PREFIX'):
                counter += 1
                percent = float(counter)/total*100
                print '%3.0f%%' % percent, line[12:-1]
        p.wait()
        print '~~~~ ~~~~~~~~~ ~~~~~~ ~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        if p.returncode != 0:
            raise RuntimeError('CPQA could not run the tests.')

    def collect_test_results(self):
        print '... Collecting test results.'
        for test_input in self._test_inputs:
            f = file(os.path.join(self.config.tstdir, test_input.prefix + '.pp'))
            test_input.tst_result = cPickle.load(f)
            f.close()

    def get_disk_usage(self):
        self.refsize = du(self.config.refdir)
        self.tstsize = du(self.config.tstdir)
