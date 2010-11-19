#!/usr/bin/env python
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

from distutils.core import setup
from glob import glob

setup(
    name='CPQA',
    version='0.0-git',
    description='CPQA is a Quality assurance framework for CP2K.',
    author='Toon Verstraelen',
    author_email='Toon.Verstraelen@UGent.be',
    url='',
    package_dir = {'cpqa': 'cpqa'},
    packages = ['cpqa'],
    scripts=glob("scripts/cpqa*.py"),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License version 3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
    ],
)
