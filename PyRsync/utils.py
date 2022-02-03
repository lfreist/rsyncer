"""
    PyRsync <https://github.com/lfreist/PyRsync.git>
    rsync.py uses systems rsync to run rsync commands from within python

    Copyright (C) 2022 Leon Freist <freist@informatik.uni-freiburg.de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from typing import Iterable, List, Any


def flatten(it: Iterable) -> List[Any]:
    """
    flat an iterable
    :param it: Iterable
    :return: Generator of flattened iterable
    """
    for i in it:
        if isinstance(i, Iterable) and not isinstance(i, (str, bytes)):
            yield from flatten(i)
        else:
            yield i
