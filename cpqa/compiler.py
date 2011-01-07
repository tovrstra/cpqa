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


__all__ = ['compile_cp2k']


def compile_cp2k(config):
    print '... Compiling CP2K.'
    make_outfn = os.path.join(os.path.abspath(config.tstdir), 'compile.log')
    f = open(make_outfn, 'w')
    p = subprocess.Popen(
        'make ARCH=%s VERSION=%s -j%i' % (config.arch, config.version, config.nproc),
        cwd=os.path.join(config.cp2k_root, 'makefiles'),
        stdout=f,
        stderr=subprocess.STDOUT,
        shell=True,
    )
    f.close()
    retcode = p.wait()
    if retcode != 0:
        raise RuntimeError('CP2K compilation failed.')
    if not os.path.isfile(config.cp2k_bin):
        raise IOError('Could not locate cp2k binary: %s' % config.cp2k_bin)
