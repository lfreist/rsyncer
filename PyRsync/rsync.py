"""
    PyBackups <https://github.com/lfreist/PyRsync.git>
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

from __future__ import annotations

from PyRsync.exceptions import DualRemoteError

from typing import List, Optional, Iterable, Any

import subprocess
import random
import os
import signal


class Syncer:
    """
    Syncer builds the rsync command and provides either a command string or a subprocess
    :param source: path to source file or dir
    :param dest: path to destination dir
    :param arguments: list of arguments used for rsync command (do not use include/exclude here!)
    :param includes: list of paths that should be included but appear to be in an excluded directory
    :param excludes: list of paths that should not be copied
    :param source_ssh: ssh connection to server where the source directory is located (e.g. "user@server.org")
    :param dest_ssh: ssh connection to server where the destination directory is located (e.g. "user@server.org")
    :param output: path to a file where rsyncy output is written to
    """

    def __init__(self,
                 source: Optional[Iterable[str], str],
                 dest: Optional[Iterable[str], str],
                 arguments: List[str] = None,
                 includes: List[str] = None,
                 excludes: List[str] = None,
                 source_ssh: str = None,
                 dest_ssh: str = None,
                 output: str = None
                 ) -> None:
        if arguments is None:
            arguments = []
        if includes is None:
            includes = []
        if excludes is None:
            excludes = []
        if source_ssh is not None and dest_ssh is not None:
            raise DualRemoteError()
        if output is None:
            self.output_file = os.path.join(os.sep, "tmp", f"syncer-{hex(random.getrandbits(32))}.tmp")
            self.save_out = False
        else:
            self.output_file = output
            self.save_out = True
        self.output = open(self.output_file, "w")
        self._arguments = ["rsync"]
        self._arguments += [
                               self._reformat_dir(source, source_ssh),
                               self._reformat_dir(dest, dest_ssh)
                           ] + [f"-{arg}" if len(arg) == 1 else f"--{arg}" for arg in arguments]
        for _dir in includes:
            self.include(_dir)
        for _dir in excludes:
            self.exclude(_dir)
        self._process = None

    def __enter__(self) -> Syncer:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # if "-P" in self.arguments:
        #    print(f"{self.get_command()}:")
        #    while self._process.poll() is None:
        #        with open(self.output_file, "rb") as f:
        #            lines = f.readlines()
        #            if len(lines) > 0:
        #                print(lines[-1][:-2].decode(), end="\r")
        #    print()
        self.close()

    def __repr__(self) -> str:
        return f"Syncer({self.get_command()})"

    def __str__(self) -> str:
        return self.get_command()

    def close(self) -> None:
        """
        Close the Syncer but hold subprocess alive
        :return: None
        """
        self.output.close()
        if not self.save_out:
            os.remove(self.output_file)

    def exit(self) -> None:
        """
        Kill subprocess and close the Syncer
        :return: None
        """
        self.kill()
        self.close()

    def _reformat_dir(self, _dir: Optional[Iterable[str], str], server: str = None) -> str:
        """
        Reformat directory string in a style, that ssh string is appended if a server is provided
        :param _dir: directory (e.g. "/path/to/file")
        :param server: ssh server with username (e.g. "user@server.org")
        :return: str (e.g. "user@server.org:/path/to/file")
        """
        if isinstance(_dir, str):
            if server is None:
                return _dir
            else:
                self._arguments.append("-a")
                return f"{server}:{_dir}"
        else:
            return " ".join([self._reformat_dir(d) for d in _dir])

    def add_argument(self, arg: str) -> None:
        """
        Add an argument to the list of arguments for rsync
        :param arg: ...
        :return: None
        """
        if arg in self._arguments:
            return
        self._arguments.append(arg)

    def include(self, _dir: str) -> None:
        """
        Include a directory
        :param _dir: path to directory as string
        :return: None
        """
        tmp = f"--include {_dir}"
        if tmp in self._arguments:
            return
        self._arguments.append(tmp)

    def exclude(self, _dir: str) -> None:
        """
        Exclude a directory or file
        :param _dir: path to directory/file as string
        :return: None
        """
        tmp = f"--exclude {_dir}"
        if tmp in self._arguments:
            return
        self._arguments.append(tmp)

    @property
    def process(self):
        return self._process

    @property
    def arguments(self) -> List[str]:
        """
        Property of Syncer._arguments
        :return: List of the rsync command
        """
        return list(flatten(self._arguments))

    def get_command(self) -> str:
        """
        Return the rsync command as copy and paste string
        :return: rsync command
        """
        return " ".join(self.arguments)

    def run(self) -> None:
        """
        run the built rsync command as a subprocess
        :return: None
        """
        self._process = subprocess.Popen(
            self.arguments,
            stdout=self.output,
            preexec_fn=os.setsid
        )

    def is_done(self) -> bool:
        """
        Returns, whether the rsync process finished or not
        :return: bool
        """
        if self._process is None:
            return False
        self._process.poll()
        if self.process.returncode:
            return True
        return False

    def kill(self) -> None:
        """
        Kill the currently running rsync process
        :return:
        """
        if self._process is None:
            print("No process started yet.")
            return
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    def progress(self) -> str:
        """
        Get rsync's '-P' progress report. You need to provide the '-P' argument to use this method.
        :return: progress
        """
        if "-P" not in self._arguments:
            print("You need to provide the '-P' argument in order to get progress data.")
            return ""
        with open(self.output_file, "r") as f:
            lines = f.readlines()
            if len(lines) > 0:
                return lines[-1]


def rsync(source: Optional[Iterable[str], str],
          dest: Optional[Iterable[str], str],
          arguments: List[str],
          includes: List[str] = None,
          excludes: List[str] = None,
          source_ssh: str = None,
          dest_ssh: str = None,
          output: str = None) -> bool:
    """
    Using the Syncer class to provide a single static functions that runs rsync commands.
    :param source: path to source file or dir
    :param dest: path to destination dir
    :param arguments: list of arguments used for rsync command (do not use include/exclude here!)
    :param includes: list of paths that should be included but appear to be in an excluded directory
    :param excludes: list of paths that should not be copied
    :param source_ssh: ssh connection to server where the source directory is located (e.g. "user@server.org")
    :param dest_ssh: ssh connection to server where the destination directory is located (e.g. "user@server.org")
    :param output: path to a file where rsyncy output is written to
    :return: Bool: True, if rsync run successfully, else False
    """
    with Syncer(source, dest, arguments, includes, excludes, source_ssh, dest_ssh, output) as sync:
        sync.run()
        p = sync.process
        p.wait()
        if p.returncode != 0:
            print(f"There was an error running rsync: Exitcode {p.returncode}")
            return False
    return True


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
