"""
    PyBackups <https://github.com/lfreist/PyBackups.git>
    Unittests for rsync.Syncer

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

import shutil
import unittest
import os

from ..PyRsync import rsync


class TestSyncer(unittest.TestCase):
    def setUp(self) -> None:
        """
        Build the following structure for subsequent tests:
        - /tmp/
          - PyRsyncSource/
            - subdir1/
              - dat1.txt
              - dat2.txt
            - subdir2/
              - dat.txt
            - file1.txt
            - file2.txt
          - PyRsyncDest/
        """
        os.mkdir(os.path.join(os.sep, "tmp", "PyRsyncSource"))
        with open(os.path.join(os.sep, "tmp", "PyRsyncSource", "file1.txt")) as f:
            f.writelines(["line 1", "line 2"])
        with open(os.path.join(os.sep, "tmp", "PyRsyncSource", "file2.txt")) as f:
            f.writelines(["Zeile 1", "Zeile 2"])
        os.mkdir(os.path.join(os.sep, "tmp", "PyRsyncSource", "subdir1"))
        os.mkdir(os.path.join(os.sep, "tmp", "PyRsyncSource", "subdir2"))
        with open(os.path.join(os.sep, "tmp", "PyRsyncSource", "subdir1", "dat1.txt")) as f:
            f.writelines(["line 1", "line 2"])
        with open(os.path.join(os.sep, "tmp", "PyRsyncSource", "subdir1", "dat2.txt")) as f:
            f.writelines(["line 1", "line 2"])
        with open(os.path.join(os.sep, "tmp", "PyRsyncSource", "subdir2", "dat.txt")) as f:
            f.writelines(["line 1", "line 2"])
        os.mkdir(os.path.join(os.sep, "tmp", "PyRsyncDest"))

    def tearDown(self) -> None:
        shutil.rmtree(os.path.join(os.sep, "tmp", "PyRsyncSource"))
        shutil.rmtree(os.path.join(os.sep, "tmp", "PyRsyncDest"))

    def syncSingleFile(self):
        with rsync.Syncer(source="/tmp/PyRsyncSource/file1.txt", dest="/tmp/PyRsyncDest") as s:
            self.assertEqual(s.get_command(), "rsync /tmp/PyRsyncSource/file1.txt /tmp/PyRsyncDest")
            s.run()
            while not s.is_done():
                pass
        self.assertListEqual(os.listdir("/tmp/PyRsyncDest"), ["file1.txt"])
