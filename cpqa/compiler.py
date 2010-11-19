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


import os


__all__ = ['compile_cp2k']


def compile_cp2k(config):
    print '... Compiling CP2K.'
    make_outfn = os.path.join(os.path.abspath(config.tstdir), 'compile.log')
    retcode = os.system('cd %s; cd makefiles; make ARCH=%s VERSION=%s -j %i 2>&1 > %s' % (
        config.cp2k_root, config.arch, config.version, config.nproc, make_outfn
    ))
    if retcode != 0:
        raise RuntimeError('CP2K compilation failed.')
