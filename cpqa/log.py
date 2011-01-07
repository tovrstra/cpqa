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


import os, difflib


__all__ = ['log_txt', 'log_html', 'diff_txt', 'diff_html']


def log_txt(runner, timer, f=None):
    config = runner.config
    if f is None:
        f = open(os.path.join(config.tstdir, 'cpqa.log'), 'w')
        print '... Writing text log:', f.name
        do_close = True
    else:
        do_close = False

    print >> f, 'Total wall time [s]: %.2f' % timer.seconds
    print >> f, 'Disk usage in ref-... [Mb]: %.2f' % (runner.refsize/1048576.0)
    print >> f, 'Disk usage in tst-... [Mb]: %.2f' % (runner.tstsize/1048576.0)

    # Extended overview
    for test_input in runner.test_inputs:
        result = test_input.tst_result
        if not result.flags['ok']:
            print >> f, '~'*80
            print >> f, 'Problems with %s' % test_input.path_inp
            if result.flags['error']:
                print >> f, ' * Something went wrong in the CPQA driver script.'
                counter = 0
                for message in result.messages:
                    for line in message.split('\n'):
                        print >> f, '    %03i|%s' % (counter, line)
                    counter += 1
            if result.flags['different'] or result.flags['wrong']:
                print >> f, ' * Some values are wrong and/or different compared to the reference.'
                for test in result.tests:
                    if test.wrong or test.different:
                        print >> f, '    %s' % test.get_command()
                        print >> f, '    !!!',
                        if test.wrong:
                            print >> f, 'WRONG',
                        if test.different:
                            print >> f, 'DIFFERENT',
                        print >> f, '!!!'
                        test.log_txt(f)
            if result.flags['missing']:
                print >> f, ' * Some values in the output could not be found'
                for test in result.tests:
                    if not test.complete(result.flags['new']):
                        print >> f, '    %s' % test.get_command()
            if result.flags['failed']:
                print >> f, ' * CP2K gave a non-zero return code.'
                print >> f, '   ----- last 20 lines of output -----'
                for line in result.last_out_lines:
                    print >> f, line
            if result.flags['verbose']:
                print >> f, ' * CP2K gave some standard output/error.'
                print >> f, '   ----- last 20 lines of standard output -----'
                for line in result.last_stdout_lines:
                    print >> f, line
                print >> f, '   ----- last 20 lines of standard error -----'
                for line in result.last_stderr_lines:
                    print >> f, line
            if result.flags['leak']:
                print >> f, ' * Some memory leaks were detect. Check the stderr.'
            print >> f, '~'*80

    # Short summary
    counters = {}
    for test_input in runner.test_inputs:
        result = test_input.tst_result
        for key in result.flags:
            counters[key] = result.flags[key] + counters.get(key, 0)
    print >> f, '='*80
    for key, value in sorted(counters.iteritems()):
        if value > 0:
            value_str = '%5i' % value
        else:
            value_str = '    -'
        print >> f, ' %1s %10s %5s' % (key[0].upper(), key.upper(), value_str)
    print >> f, '   %10s %5i' % ('TOTAL', len(runner.test_inputs))
    print >> f, '='*80

    if do_close:
        f.close()

css = """
body { font-family: sans; font-size: 10pt; }
td { border: solid 1px #666; text-align: right; padding: 3px 3px; white-space: nowrap; }
th { border: solid 1px #666; text-align: right; padding: 3px 3px; white-space: nowrap; }
table { border-collapse: collapse; border: solid 1px black; font-size: 10pt; }
p.cat { color: #800; }
.grey { background-color: #AAA; }
.green { background-color: #AFA; }
.red { background-color: #FAA; }
.purple { background-color: #FAF; }
//tr { border: solid 1px #666; }
"""

def log_html(runner, timer):
    config = runner.config
    f = open(os.path.join(config.tstdir, 'index.html'), 'w')
    print '... Writing html log:', f.name
    print >> f, '<html><head>'
    print >> f, '<title>CPQA log</title>'
    print >> f, '<style type="text/css">%s</style>' % css
    print >> f, '</head><body>'
    print >> f, '<h1>CPQA log</h1>'

    print >> f, '<h2>General info</h2>'
    print >> f, '<table>'
    print >> f, '<tr><th>CP2K Root</th><td>%s</td></tr>' % config.cp2k_root
    print >> f, '<tr><th>Arch</th><td>%s</td></tr>' % config.arch
    print >> f, '<tr><th>Version</th><td>%s</td></tr>' % config.version
    print >> f, '<tr><th>NProc</th><td>%i</td></tr>' % config.nproc
    if config.mpi_prefix is not None:
        print >> f, '<tr><th>NProc MPI</th><td>%i</td></tr>' % config.nproc_mpi
        print >> f, '<tr><th>MPI prefix</th><td>%s</td></tr>' % config.mpi_prefix
    print >> f, '<tr><th>Reference directory</th><td>%s</td></tr>' % config.refdir
    print >> f, '<tr><th>Test directory</th><td>%s</td></tr>' % config.tstdir
    for select_dir in config.select_dirs:
        print >> f, '<tr><th>Select dir</th><td>%s</td></tr>' % select_dir
    for select_path_inp in config.select_paths_inp:
        print >> f, '<tr><th>Select path inp</th><td>%s</td></tr>' % select_path_inp
    if config.faster_than is not None:
        print >> f, '<tr><th>Faster than</th><td>%.2fs</td></tr>' % config.faster_than
    if config.slower_than is not None:
        print >> f, '<tr><th>Slower than</th><td>%.2fs</td></tr>' % config.slower_than
    print >> f, '<tr><th>Number of test jobs</th><td>%i</td></tr>' % len(runner.test_inputs)
    print >> f, '<tr><th>Total wall time [s]</th><td>%.2f</td></tr>' % timer.seconds
    print >> f, '</table>'

    print >> f, '<h2>Summary</h2>'
    print >> f, '<table>'
    print >> f, '<tr><th>Flag</th><th>Label</th><th>Count</th></tr>'
    counters = {}
    for test_input in runner.test_inputs:
        result = test_input.tst_result
        for key in result.flags:
            counters[key] = result.flags[key] + counters.get(key, 0)
    for key, value in sorted(counters.iteritems()):
        if value > 0:
            value_str = '%i' % value
        else:
            value_str = '-'
        print >> f, '<tr><td>%1s</td><td>%10s</td><td>%s</td></tr>' % (key[0].upper(), key.upper(), value_str)
    print >> f, '<tr><td>&nbsp;</td><td>%10s</td><td>%i</td></tr>' % ('TOTAL', len(runner.test_inputs))
    print >> f, '</table>'

    print >> f, '<h2>Regressions</h2>'
    for test_input in runner.test_inputs:
        result = test_input.tst_result
        if not result.flags['ok']:
            print >> f, '<h3>%s</h3>' % test_input.path_inp
            print >> f, '<p><a href=\'%s\'>%s</a></p>' % (test_input.path_out, test_input.path_out)
            if result.flags['error']:
                print >> f, '<p class="cat">Something went wrong in the CPQA driver script.</p>'
                print >> f, '<ol>'
                for message in result.messages:
                    print >> f, '<li><pre>%s</pre></li>' % message
                print >> f, '</ol>'
            if result.flags['wrong'] or result.flags['different']:
                print >> f, '<p class="cat">Some values are wrong and/or different compared to the reference.</p>'
                if result.flags['different']:
                    fn_html_diff = diff_html_file(config, test_input)
                    print >> f, '<p>Full diff: <a href="%s">%s</a>' % (fn_html_diff, fn_html_diff)
                print >> f, '<ol>'
                for test in result.tests:
                    if test.wrong or test.different:
                        print >> f, '<li><pre>%s</pre>' % test.get_command(),
                        if test.wrong:
                            print >> f, '<b>WRONG</b>',
                        if test.different:
                            print >> f, '<b>DIFFERENT</b>',
                        print >> f, '<br /><pre>'
                        test.log_html(f)
                        print >> f, '</pre></li>'
                print >> f, '</ol>'
            if result.flags['missing']:
                print >> f, '<p class="cat">Some values in the output could not be found.</p>'
                print >> f, '<ol>'
                for test in result.tests:
                    if not test.complete(result.flags['new']):
                        print >> f, '<li><pre>%s</pre></li>' % test.get_command()
                print >> f, '</ol>'
            if result.flags['failed']:
                print >> f, '<p class="cat">CP2K gave a non-zero return code.</p>'
                print >> f, '<p>Last 20 lines of output:</p>'
                print >> f, '<pre class="grey">'
                for line in result.last_out_lines:
                    print >> f, line
                print >> f, '</pre>'
            if result.flags['verbose']:
                print >> f, '<p class="cat">CP2K gave some standard output/error.</p>'
                print >> f, '<p>Last 20 lines of standard output:</p>'
                print >> f, '<pre class="grey">'
                for line in result.last_stdout_lines:
                    print >> f, line
                print >> f, '</pre>'
                print >> f, '<p>Last 20 lines of standard error:</p>'
                print >> f, '<pre class="grey">'
                for line in result.last_stderr_lines:
                    print >> f, line
                print >> f, '</pre>'
            if result.flags['leak']:
                print >> f, '<p class="cat">Some memory leaks were detect. Check the stderr.</p>'

    print >> f, '</body></html>'
    f.close()


def diff_txt(f, old, new, oldname, newname, indent=''):
    red = "\033[0;31m"
    green = "\033[0;32m"
    reset = "\033[m"
    print >> f, indent + ('Diff from %s to %s:' % (oldname, newname))
    for line in difflib.ndiff(old, new):
        if line.startswith('+'):
            if f.isatty():
                print >> f, green + line[:-1] + reset
            else:
                print >> f, line[:-1]
        elif line.startswith('-'):
            if f.isatty():
                print >> f, red + line[:-1] + reset
            else:
                print >> f, line[:-1]

def diff_html(f, old, new, oldname, newname):
    print >> f, '<pre>'
    for line in difflib.unified_diff(old, new, oldname, newname):
        line = line[:-1]
        if line.startswith('---'):
            open_tag = '<b class="red">'
            close_tag = '</b>'
        elif line.startswith('+++'):
            open_tag = '<b class="green">'
            close_tag = '</b>'
        elif line.startswith('-'):
            open_tag = '<span class="red">'
            close_tag = '</span>'
        elif line.startswith('+'):
            open_tag = '<span class="green">'
            close_tag = '</span>'
        elif line.startswith('@@') and line.endswith('@@'):
            open_tag = '<i class="purple">'
            close_tag = '</i>'
        else:
            open_tag = ''
            close_tag = ''
        print >> f, open_tag + line + close_tag
    print >> f, '</pre>'


def diff_html_file(config, test_input):
    f_ref = open(os.path.join(config.refdir, test_input.path_out))
    ref_lines = f_ref.readlines()
    f_ref.close()
    f_tst = open(os.path.join(config.tstdir, test_input.path_out))
    tst_lines = f_tst.readlines()
    f_tst.close()

    f_html = open(os.path.join(config.tstdir, test_input.path_out + '.diff.html'), 'w')
    print '... Writing html log:', f_html.name
    print >> f_html, '<html><head>'
    print >> f_html, '<title>Diff for %s</title>' % test_input.path_out
    print >> f_html, '<style type="text/css">%s</style>' % css
    print >> f_html, '</head><body>'
    print >> f_html, '<h2>Diff for %s</h2>' % test_input.path_out
    diff_html(f_html, ref_lines, tst_lines, 'ref', 'tst')
    print >> f_html, '</body></html>'
    f_html.close()

    return test_input.path_out + '.diff.html'
