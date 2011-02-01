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


import os, subprocess


__all__ = ['update_source', 'compile_program']


def update_source(config):
    if config.cvs_update is None:
        print '... Skipping source code update.'
    else:
        print '... Updating to latest version of the source.'
        cvs_outfn = os.path.join(os.path.abspath(config.tstdir), 'cvs.log')
        f = open(cvs_outfn, 'w')
        p = subprocess.Popen(
            config.cvs_update,
            cwd=os.path.join(config.root),
            stdout=f,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        f.close()


def compile_program(config):
    print '... Compiling.'
    make_outfn = os.path.join(os.path.abspath(config.tstdir), 'compile.log')
    f = open(make_outfn, 'w')
    p = subprocess.Popen(
        config.make,
        cwd=config.makedir,
        stdout=f,
        stderr=subprocess.STDOUT,
        shell=True,
    )
    f.close()
    retcode = p.wait()
    if retcode != 0:
        raise RuntimeError('Compilation failed.')
    if not os.path.isfile(config.bin):
        raise IOError('Could not locate binary: %s' % config.bin)
