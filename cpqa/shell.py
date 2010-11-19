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


__all__ = ['du', 'tail']


def du(dirname):
    result = 0
    for dirpath, dirnames, filenames in os.walk(dirname):
        result += sum(
            os.path.getsize(os.path.join(dirpath, fn))
            for fn in filenames
        )
    return result


def tail(fn, lines=20):
    # Taken from stackoverflow with some small changes.
    # http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
    f = open(fn)
    f.seek(0, 2)
    size = f.tell()
    lines_found = 0
    data = ''
    while lines+1 > lines_found and size > len(data):
        read_size = min(1024, size-len(data))
        f.seek(-(read_size+len(data)), 2)
        new_data = f.read(read_size)
        data = new_data + data
        lines_found += new_data.count('\n')
    f.close()
    if len(data) == 0:
        return []
    else:
        return data.split('\n')[-lines:]
