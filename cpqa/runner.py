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


import os, subprocess, shutil, cPickle, copy

from cpqa.shell import du


__all__ = ['Runner']


class Runner(object):
    def __init__(self, work):
        self.work = work
        self.config = work.config
        test_inputs = self.config.filter_inputs_name(self.work.test_inputs)
        self.load_references(test_inputs)
        self.test_inputs = self.config.filter_inputs_timing(test_inputs)
        self.select_dependencies()
        self.sort_test_inputs()
        self.copy_inputs()
        #self.create_makefile()
        #self.run_makefile()
        self.run_tests()
        self.collect_test_results()
        self.get_disk_usage()

    def load_references(self, test_inputs):
        # Try to get the reference results.
        for test_input in test_inputs:
            fn = os.path.join(self.config.refdir, test_input.path_pp)
            if os.path.isfile(fn):
                f = file(fn)
                test_input.ref_result = cPickle.load(f)
                f.close()
            else:
                test_input.ref_result = None

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
        original = set(self.test_inputs)
        extra = self._with_dependencies(original) - original
        self.load_references(extra)
        self.test_inputs.extend(extra)
        print '... Total number of jobs: %i' % len(self.test_inputs)

    def sort_test_inputs(self):
        # First compute the timing including the dependencies.
        for test_input in self.test_inputs:
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
        self.test_inputs.sort(compare, reverse=True)

    def copy_inputs(self):
        print '... Copying inputs and related files.'
        # Copy only the input files needed to run this batch of tests.
        # - First make a complete list of paths, including the extra_inputs
        all_paths = set([])
        for test_input in self.test_inputs:
            all_paths.add(test_input.path_inp)
            for path_extra in test_input.paths_extra:
                all_paths.add(path_extra)
        # - Then copy the stuff
        for path in all_paths:
            src_path = os.path.join(self.config.indir, path)
            dirname = os.path.dirname(path)
            dst_dir = os.path.join(self.config.tstdir, dirname)
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)
            shutil.copy(src_path, dst_dir)

    def run_tests(self):
        if self.config.mpi_prefix is None:
            max_task = self.config.nproc
        else:
            max_task = self.config.nproc/self.config.nproc_mpi
        todo = copy.copy(self.test_inputs)
        running = {}
        done = set([])
        print '~~~~ ~~~~~~~~~~ ~~~~~~ ~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        print 'Prog   Flags    Binary Script Test'
        print '~~~~ ~~~~~~~~~~ ~~~~~~ ~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
        counter = 0.0
        total = len(todo)
        waiting = False # Indicate that we are currently waiting on dependencies
        while len(todo) > 0 or len(running) > 0:
            # If len(running)==max_task wait for a job to finnish
            if len(running) >= max_task or len(todo) == 0 or waiting:
                pid, retcode = os.wait()
                p, test_input = running.pop(pid)
                lines = p.stdout.readlines()
                if retcode != 0:
                    print 'Test driver script returned a non-zero exit code'
                    for line in lines:
                        print line[:-1]
                else:
                    for line in lines:
                        if line.startswith('CPQA-PREFIX'):
                            counter += 1
                            percent = float(counter)/total*100
                            print '%3.0f%%' % percent, line[12:-1]
                            break
                done.add(test_input)
            waiting = False
            # Just continue if the todo list is empty
            if len(todo) == 0:
                continue
            # Take a new test input. If none can be found, all todo items are
            # waiting for dependencies.
            test_input = None
            for i in xrange(len(todo)):
                accepted = True
                for depend in todo[i].depends:
                    if depend not in done:
                        accepted = False
                        break
                if accepted:
                     test_input = todo.pop(i)
                     break
            if test_input is None:
                waiting = True
                continue
            # Launch the new job
            if self.config.mpi_prefix is None:
                args = [
                    'cpqa-driver.py',
                    os.path.abspath(self.config.bin),
                    test_input.path_inp, self.config.refdir
                ]
            else:
                args = [
                    'cpqa-driver.py',
                    os.path.abspath(self.config.bin),
                    test_input.path_inp, self.config.refdir,
                    self.config.mpi_prefix
                ]
            p = subprocess.Popen(args, cwd=self.config.tstdir, stdout=subprocess.PIPE)
            running[p.pid] = (p, test_input)
        print '~~~~ ~~~~~~~~~~ ~~~~~~ ~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'

    def collect_test_results(self):
        print '... Collecting test results.'
        for test_input in self.test_inputs:
            fn = os.path.join(self.config.tstdir, test_input.path_pp)
            if os.path.isfile(fn):
                f = file(os.path.join(self.config.tstdir, test_input.path_pp))
                test_input.tst_result = cPickle.load(f)
                f.close()
            else:
                print 'Could not find', fn
                test_input.tst_result = None

    def get_disk_usage(self):
        self.refsize = du(self.config.refdir)
        self.tstsize = du(self.config.tstdir)
