"""
    rsyncer <https://github.com/lfreist/rsyncer.git>
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

from rsyncer.exceptions import DualRemoteError, RsyncError

from typing import List, Optional, Iterable, Any, Union

import subprocess
import os
import signal
import tempfile
import pathlib

# this is just for development purposes
_valid_args = (
    "verbose", "msgs2stderr", "quiet", "no-motd", "checksum", "archive", "recursive", "relative", "no-implied-dirs",
    "backup", "backup-dir", "update", "inplace", "append", "append-verify", "dirs", "links", "copy-links", "fuzzy",
    "copy-unsafe-links", "safe-links", "munge-links", "copy-dirlinks", "keep-dirlinks", "hard-links", "perms",
    "executability", "acls", "xattrs", "owner", "group", "devices", "specials", "times", "omit-dir-times",
    "omit-link-times", "super", "fake-super", "sparse", "preallocate", "dry-run", "whole-file", "one-file-system",
    "existing", "ignore-existing", "remove-source-files", "del", "delete", "delete-before", "delete-during",
    "delete-delay", "delete-after", "delete-excluded", "ignore-missing-args", "delete-missing-args", "force",
    "ignore-errors", "partial", "delay_updates", "prune-empty-dirs", "numeric-ids", "ignore-times", "size-only",
    "compress", "cvs-exclude", "from0", "protect-args", "blocking-io", "stats", "8-bit-output", "human-readable",
    "progress", "itemize-changes", "list-only", "noatime", "ipv4", "ipv6", "version", "help"
)
_valid_kwargs = (
    "info", "debug", "backup_dir", "suffix", "chmod", "checksum_choice", "block_size", "rsh", "rsync_path",
    "max_delete", "max_size", "min_size", "partial_dir", "usermap", "grupmap", "chown", "timeout", "contimeout",
    "modify_window", "temp_dir", "compare_dest", "copy_dest", "link_dest", "compress_level", "skip-compress",
    "filter", "exclude", "exclude_from", "include", "include_from", "files_from", "address", "port", "sockopts",
    "outbuf", "remote_option", "out_format", "log_file", "log_file_format", "password_file", "bwlimit", "stop_at",
    "time_limit", "write_batch", "only_write_batch", "read_batch", "protocol", "iconv", "checksum_seed"
)


class Syncer:
    """
    Syncer builds the rsync command and provides either a command string or a subprocess
    :param source: path to source file or dir
    :param dest: path to destination dir
    :param rsync_pth: path to rsync (e.g. "/usr/bin/rsync")
    :param source_ssh: ssh connection to server where the source directory is located (e.g. "user@server.org")
    :param dest_ssh: ssh connection to server where the destination directory is located (e.g. "user@server.org")
    :param output: path to a file where rsync output is written to
    :param **kwargs: take any rsync option with value (value must be True if option does not take a value)
    """

    def __init__(self,
                 source: Union[Iterable[str], str],
                 dest: Union[Iterable[str], str],
                 rsync_path: str = "rsync",
                 source_ssh: str = None,
                 dest_ssh: str = None,
                 output: str = None,
                 **kwargs
                 ) -> None:
        if source_ssh is not None and dest_ssh is not None:
            raise DualRemoteError()
        self._source = self._reformat_dir(source, source_ssh)
        self._dest = self._reformat_dir(dest, dest_ssh)
        self._rsync_path = rsync_path
        if output is None:
            self.output_file = tempfile.TemporaryFile("w+")
            self.save_out = False
        else:
            self.output_file = open(output, "w")
            self.save_out = True
        self._arguments = []
        for name, value in kwargs.items():
            self._arguments += self._parse_arg(name, value)
        self._process = None

    def get_cmd_list(self) -> List[str]:
        """
        Build subprocess usable list.
        Example:
        > command_list() -> ["rsync", "--arg1", "--arg2 opt"]

        :return: List[str]
        """
        return [self._rsync_path, self._source, self._dest] + self._arguments

    @staticmethod
    def _parse_arg(name: str, value: str = None) -> List[str]:
        """
        Parse kwarg to string.
        Examples:
        > Syncer._parse_arg("exclude", "path/")              -> ["--exclude path/"]
        > Syncer._parse_arg("exclude", ["path/1", "path/2"]) -> ["--exclude path/1 --exclude path/2"]
        > Syncer._parse_arg("verbose")                       -> ["--verbose"]
        > Syncer._parse_arg("v")                             -> ["-v"]

        :param name: Name of the argument
        :param value: Option/Value for the argument
        :return: List[str]
        """
        if isinstance(value, bool):
            value = None
        name = name.replace("_", "-")
        if len(name) == 1:
            name = f"-{name}"
        else:
            name = f"--{name}"
        if isinstance(value, Iterable) and not isinstance(value, str):
            return list(map(lambda v: f"{name} {v}", value))
        return [f"{name}"] if value is None else [f"{name} {value}"]

    def _reformat_dir(self, _dir: Union[Iterable[str], str], server: str = None) -> str:
        """
        Reformat directory string in a style, that ssh string is appended if a server is provided.
        Example:
        > Syncer._reformat_dir("/path/to/dir", "user@server.domain") -> "user@server.domain:/path/to/dir"

        :param _dir: directory (e.g. "/path/to/dir")
        :param server: ssh server with username (e.g. "user@server.org")
        :return: str
        """
        if isinstance(_dir, str):
            if server is None:
                return _dir
            else:
                return f"{server}:{_dir}"
        else:
            return " ".join([self._reformat_dir(d) for d in _dir])

    def __enter__(self) -> Syncer:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Syncer({self.get_command()})"

    def __str__(self) -> str:
        return " ".join(self.get_cmd_list())

    def get_shell_command(self) -> str:
        """
        Get the rsync command in string format for copy & paste into the terminal
        :return:
        """
        return str(self)

    def close(self) -> None:
        """
        Close the Syncer but hold subprocess alive
        :return: None
        """
        self.output_file.close()

    def exit(self) -> None:
        """
        Kill subprocess and close the Syncer
        :return: None
        """
        self.kill()
        self.close()

    def add_argument(self, **kwargs) -> None:
        """
        Add an argument to the list of arguments for rsync
        :param kwarg: ...
        :return: None
        """
        for name, value in kwargs.items():
            tmp = self._parse_arg(name, value)
            if tmp not in self._arguments:
                self._arguments += self._parse_arg(name, value)

    def run(self) -> None:
        """
        run the built rsync command as a subprocess
        :return: None
        """
        self._process = subprocess.Popen(
            self.get_cmd_list(),
            stdout=self.output_file,
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
        return self._process.returncode is not None

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
        TODO: implement
        Get rsync's '-P' progress report. You need to provide the '-P' argument to use this method.
        :return: progress
        """
        if "-P" not in self._arguments:
            print("You need to provide the '-P' argument in order to get progress data.")
            return ""

    @property
    def process(self):
        return self._process


def rsync(source: Union[Iterable[str], str],
          dest: Union[Iterable[str], str],
          rsync_path: str = "rsync",
          source_ssh: str = None,
          dest_ssh: str = None,
          output: str = None,
          **kwargs) -> bool:
    """
    Using the Syncer class to provide a single static functions that runs rsync commands.
    :param source: path to source file or dir
    :param dest: path to destination dir
    :param rsync_path: path to rsync executable
    :param source_ssh: ssh connection to server where the source directory is located (e.g. "user@server.org")
    :param dest_ssh: ssh connection to server where the destination directory is located (e.g. "user@server.org")
    :param output: path to a file where rsyncy output is written to
    :param **kwargs: Any rsync option with value (value must be True if option does not take a value)
    :return: Bool: True, if rsync run successfully, else False
    """
    with Syncer(source, dest, rsync_path, source_ssh, dest_ssh, output, **kwargs) as sync:
        print(sync.get_command())
        sync.run()
        p = sync.process
        p.wait()
        if p.returncode != 0:
            print(f"There was an error running rsync: Exitcode {p.returncode}")
            return False
    return True


# ----------------------------------------------------------------------------------------------------------------------

def get_multi_thread_dirs(rsync_cmd_list) -> List[List[str]]:
    if "--dry-run" not in rsync_cmd_list and "-n" not in rsync_cmd_list:
        rsync_cmd_list.append("--dry-run")
    dry_run = subprocess.run(rsync_cmd_list, stdout=subprocess.PIPE)
    if dry_run.returncode != 0:
        raise RsyncError
    print("----")
    for line in dry_run.stdout.decode().split("\n"):
        line = pathlib.Path(line)
        # TODO: implement
    return []
