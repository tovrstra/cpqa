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

import sys, os
from optparse import OptionParser


usage = """Usage: %prog some.inp dependency.inp

This script adds a dependency tag to the file 'some.inp' such that it is
executed after 'dependency.inp'.
"""

def parse_args():
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args) != 2:
        raise TypeError('Expecting two arguments')
    if not (os.path.isfile(args[0]) and os.path.isfile(args[1])):
        raise ValueError('Both arguments must be existing files.')
    if not (args[0].endswith('.inp') and args[1].endswith('.inp')):
        raise ValueError('Both arguments must be input files.')
    return args


def main():
    args = parse_args()
    # read the first file
    f = open(args[0])
    data = f.read()
    f.close()
    # write the CPQA directive and the original contents
    f = open(args[0], 'w')
    f.write('#CPQA DEPENDS %s\n' % args[1])
    f.write(data)
    f.close()


if __name__ == '__main__':
    main()
