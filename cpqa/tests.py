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


import os, re, sys, traceback, numpy

from cpqa.log import diff_html, diff_txt
from cpqa.shell import tail


__all__ = [
    'test_factories', 'harvest_test'
]


class Fragment(object):
    def __init__(self):
        self.lines = []

    def feed(self, line):
        raise NotImplementedError

    def digest(self):
        raise NotImplementedError

    def complete(self):
        raise NotImplementedError


class ScalarFragment(Fragment):
    def __init__(self, regex, column):
        self.regex = regex
        self.compiled = re.compile(regex)
        self.column = column
        self.lines = []
        self.value = None
        Fragment.__init__(self)

    def feed(self, line):
        match = self.compiled.search(line)
        if match is not None:
            self.lines = [line]

    def digest(self):
        if len(self.lines) == 1:
            self.value = float(self.lines[0].split()[self.column])

    def complete(self):
        return self.value is not None


class ArrayFragment(Fragment):
    def __init__(self, regex_start, regex_stop, columns, skip=0):
        self.regex_start = regex_start
        self.compiled_start = re.compile(regex_start)
        self.regex_stop = regex_stop
        self.compiled_stop = re.compile(regex_stop)
        self.columns = columns
        self.skip = skip
        # internal stuff
        self.status = 0
        self.lines = []

    def feed(self, line):
        if self.status == 0 and (self.compiled_start.search(line) is not None):
            self.status = 1
            self.toskip = self.skip
            self.lines = []
        elif self.status == 1:
            if (self.compiled_stop.search(line) is not None):
                self.status = 0
            elif self.toskip > 0:
                self.toskip -= 1
            else:
                self.lines.append(line)

    def digest(self):
        if len(self.lines) > 0:
            data = []
            for line in self.lines:
                row = []
                words = line.split()
                for c in self.columns:
                    row.append(float(words[c]))
                data.append(row)
            self.data = numpy.array(data)
        else:
            self.data = None


def harvest_test(test_input, refdir, new, messages):
    if not new:
        path_out = os.path.join(refdir, test_input.path_out)
        fragments = [test.ref for test in test_input.tests if hasattr(test, 'ref')]
        harvest_file(path_out, fragments, messages)
    fragments = [test.tst for test in test_input.tests if hasattr(test, 'tst')]
    harvest_file(test_input.path_out, fragments, messages)
    for test in test_input.tests:
        try:
            test.harvest_other(test_input, messages)
        except Exception, e:
            messages.append(traceback.format_exc())


def harvest_file(path_out, fragments, messages):
    if not os.path.isfile(path_out):
        return
    f = file(path_out)
    for line in f:
        for fragment in fragments:
            fragment.feed(line)
    f.close()
    for fragment in fragments:
        try:
            fragment.digest()
        except Exception, e:
            messages.append(traceback.format_exc())



class Test(object):
    def __init__(self, directive, fns_extra=None):
        self.directive = directive
        self.wrong = None
        self.different = None
        if fns_extra is None:
            self.fns_extra = []
        else:
            self.fns_extra = fns_extra

    def get_command(self):
        raise NotImplementedError

    def harvest_other(self, test_input, messages):
        pass

    def complete(self, new):
        raise NotImplementedError

    def run(self, new):
        raise NotImplementedError

    def log_txt(self, f):
        raise NotImplementedError

    def log_html(self, f):
        raise NotImplementedError


class ScalarTest(Test):
    def __init__(self, directive, regex, column, exp_value=None, threshold=1e-15):
        self.regex = regex
        self.compiled = re.compile(regex)
        self.column = column
        self.exp_value = exp_value
        self.threshold = threshold
        self.ref = ScalarFragment(regex, column)
        self.tst = ScalarFragment(regex, column)
        Test.__init__(self, directive)

    def get_command(self):
        if self.exp_value is None:
            return '%s \'%s\' %i' % (
                self.directive.upper(), self.regex, self.column
            )
        else:
            return '%s \'%s\' %i %s %s' % (
                self.directive.upper(), self.regex, self.column,
                self.exp_value, self.threshold
            )

    def complete(self, new):
        return self.tst.complete() and (new or self.ref.complete())

    def run(self, new):
        if not new:
            self.ref_error = self.tst.value - self.ref.value
            if self.ref.value == 0.0:
                self.different = self.tst.value != 0.0
            else:
                self.different = abs(self.ref_error/self.ref.value) > 1e-15
        else:
            self.different = None

        if self.exp_value is not None:
            self.exp_error = self.tst.value - self.exp_value
            if self.exp_value == 0.0:
                self.wrong = abs(self.tst.value) > self.threshold
            else:
                self.wrong = abs(self.exp_error/self.exp_value) > self.threshold
        else:
            self.wrong = None

    def log_txt(self, f):
        if self.different is True:
            print >> f, '    tst % .8e' % self.tst.value
            if self.ref.value == 0.0:
                print >> f, '    ref % .8e    abs err % .8e' % \
                    (self.ref.value, self.ref_error)
            else:
                print >> f, '    ref % .8e    rel err % .8e' % \
                    (self.ref.value, self.ref_error/abs(self.ref.value))
            diff_txt(f, self.ref.lines, self.tst.lines, 'ref', 'tst', '    ')
        if self.wrong is True:
            print >> f, '    tst % .8e' % self.tst.value
            if self.exp_value == 0.0:
                print >> f, '    exp % .8e    abs err % .8e    threshold % .8e' % \
                    (self.exp_value, self.exp_error, self.threshold)
            else:
                print >> f, '    exp % .8e    rel err % .8e    threshold % .8e' % \
                    (self.exp_value, self.exp_error/abs(self.exp_value), self.threshold)

    def log_html(self, f):
        if self.different is True:
            print >> f, '<table>'
            print >> f, '<tr><th>tst</th><td>% .15e</td></tr>' % self.tst.value
            if self.ref.value == 0.0:
                print >> f, '<tr><th>ref</th><td>% .15e</td>' % self.ref.value
                print >> f, '<th>abs err</th><td>% .15e</td></tr>' % self.ref_error
            else:
                print >> f, '<tr><th>ref</th><td>% .15e</td>' % self.ref.value
                print >> f, '<th>abs err</th><td>% .15e</td>' % self.ref_error
                print >> f, '<th>rel err</th><td>% .15e</td></tr>' % (self.ref_error/abs(self.ref.value))
            print >> f, '</table>'
            diff_html(f, self.ref.lines, self.tst.lines, 'ref', 'tst')
        if self.wrong is True:
            print >> f, '<table>'
            print >> f, '<tr><th>tst</th><td>% .15e</td></tr>' % self.tst.value
            if self.exp_value == 0.0:
                print >> f, '<tr><th>exp</th><td>% .15e</td>' % self.exp_value
                print >> f, '<th>abs err</th><td>% .15e</td></tr>' % self.exp_error
            else:
                print >> f, '<tr><th>exp</th><td>% .15e</td>' % self.exp_value
                print >> f, '<th>abs err</th><td>% .15e</td>' % self.exp_error
                print >> f, '<th>rel err</th><td>% .15e</td></tr>' % (self.exp_error/abs(self.exp_value))
            print >> f, '</table>'


class CompareScalarTest(ScalarTest):
    def __init__(self, directive, exp_prefix, regex, column, threshold=1e-15):
        self.exp_prefix = exp_prefix
        self.exp = ScalarFragment(regex, column)
        ScalarTest.__init__(self, directive, regex, column, None, threshold)

    def get_command(self):
        return '%s %s \'%s\' %i %s' % (
            self.directive.upper(), self.exp_prefix, self.regex, self.column,
            self.threshold
        )

    def harvest_other(self, test_input, messages):
        dirname = os.path.dirname(test_input.path_inp)
        expfn = os.path.join(dirname, self.exp_prefix) + '.out'
        harvest_file(expfn, [self.exp], messages)

    def complete(self, new):
        return ScalarTest.complete(self, new) and self.exp.complete() == 1

    def run(self, new):
        self.exp_value = self.exp.value
        ScalarTest.run(self, new)

    def log_txt(self, f):
        ScalarTest.log_txt(self, f)
        if self.wrong is True:
            diff_txt(f, self.exp.lines, self.tst.lines, 'exp', 'tst', '    ')

    def log_html(self, f):
        ScalarTest.log_html(self, f)
        if self.wrong is True:
            diff_html(f, self.exp.lines, self.tst.lines, 'exp', 'tst')


class ScriptTest(Test):
    def __init__(self, directive, script, args):
        self.script = script
        self.args = args
        Test.__init__(self, directive, [script])

    def get_command(self):
        return '%s \'%s\' %s' % (self.directive.upper(), self.script, ' '.join(self.args))

    def harvest_other(self, test_input, messages):
        self.dirname = os.path.dirname(test_input.path_inp)

    def complete(self, new):
        return True

    def run(self, new):
        log_prefix = self.args[0] + '-' + self.script
        if len(self.args) > 1:
            log_prefix += '-' + '-'.join(self.args[1:])
        self.return_code = os.system('cd %s; ./%s %s > %s.stdout 2> %s.stderr' % (
            self.dirname, self.script, ' '.join(self.args), log_prefix, log_prefix
        ))
        self.wrong = self.return_code != 0
        if self.wrong is True:
            self.last_stdout_lines = tail(os.path.join(self.dirname, log_prefix + '.stdout'))
            self.last_stderr_lines = tail(os.path.join(self.dirname, log_prefix + '.stderr'))

    def log_txt(self, f):
        if self.wrong is True:
            print >> f, '    Script ended with return code %i' % self.return_code
            print >> f, '   ----- last 20 lines of standard output of the script -----'
            for line in self.last_stdout_lines:
                print >> f, line
            print >> f, '   ----- last 20 lines of standard error of the script -----'
            for line in self.last_stderr_lines:
                print >> f, line

    def log_html(self, f):
        if self.wrong is True:
            print >> f, '<p>Script ended with return code %i</p>' % self.return_code
            print >> f, '<p>Last 20 lines of standard output of the script:</p>'
            print >> f, '<pre class="grey">'
            for line in self.last_stdout_lines:
                print >> f, line
            print >> f, '</pre>'
            print >> f, '<p>Last 20 lines of standard error of the script:</p>'
            print >> f, '<pre class="grey">'
            for line in self.last_stderr_lines:
                print >> f, line
            print >> f, '</pre>'


class ScalarFactory(object):
    def __init__(self):
        self.directive = 'scalar'

    def __call__(self, words):
        if len(words) == 2:
            regex, column = words
            column = int(column)
            return ScalarTest(self.directive, regex, column)
        elif len(words) == 3:
            regex, column, exp_value = words
            column = int(column)
            exp_value = float(exp_value)
            return ScalarTest(self.directive, regex, column, exp_value)
        elif len(words) == 4:
            regex, column, exp_value, threshold = words
            column = int(column)
            exp_value = float(exp_value)
            threshold = float(threshold)
            return ScalarTest(self.directive, regex, column, exp_value, threshold)
        else:
            raise TypeError('There must be two, three or four arguments for a scalar test.')


class CompareScalarFactory(object):
    def __init__(self):
        self.directive = 'compare-scalar'

    def __call__(self, words):
        if len(words) == 3:
            prefix, regex, column = words
            column = int(column)
            return CompareScalarTest(self.directive, prefix, regex, column)
        elif len(words) == 4:
            prefix, regex, column, threshold = words
            column = int(column)
            threshold = float(threshold)
            return CompareScalarTest(self.directive, prefix, regex, column, threshold)
        else:
            raise TypeError('There must be three arguments for a custom scalar comparison.')


class ScriptFactory(object):
    def __init__(self):
        self.directive = 'script'

    def __call__(self, words):
        if len(words) >= 2:
            script = words[0]
            args = words[1:]
            return ScriptTest(self.directive, script, args)
        else:
            return TypeError('A script test requires at least two arguments.')


test_factories = [
    ScalarFactory(),
    CompareScalarFactory(),
    ScriptFactory(),
]
test_factories = dict((test.directive, test) for test in test_factories)
