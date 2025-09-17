# SPDX-FileCopyrightText: 2023-2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

"""Basic logging functions utilizing the rich.console module."""

__all__ = ['set_console']

import sys
from typing import IO, Any, Optional

from rich.console import Console

console_stderr = None
console_stdout = None
debug_on = False


def _print_stdout(*args: Any) -> None:
    if console_stdout is not None:
        console_stdout.print(*args)  # type: ignore


def _print_stderr(*args: Any) -> None:
    if console_stderr is not None:
        console_stderr.print(*args)  # type: ignore


def err(*args: Any) -> None:
    _print_stderr('[red]error: ', *args)  # type: ignore


def warn(*args: Any) -> None:
    _print_stderr('[yellow]warning: ', *args)  # type: ignore


def die(*args: Any) -> None:
    err(*args)
    sys.exit(1)


def debug(*args: Any) -> None:
    if debug_on:
        _print_stderr('[bright_blue]debug: ', *args)  # type: ignore


def eprint(*args: Any) -> None:
    _print_stderr(*args)  # type: ignore


def print(*args: Any) -> None:
    _print_stdout(*args)  # type: ignore


def set_console(file_stdout: Optional[IO[str]]=None,
                file_stderr: Optional[IO[str]]=None,
                quiet: bool=False,
                no_color: bool=False,
                force_terminal: Optional[bool]=None,
                debug: bool=False) -> None:
    """Configure rich console properties used by esp_idf_size

    Args:
      file_stdout:
        A file object where the console should write stdout to. Defaults to `None`, meaning stdout.
      file_stderr:
        A file object where the console should write stderr to. Defaults to `None`, meaning stderr.
      quiet:
        Enable/disable all output. Defaults to False.
      no_color:
        Enable/disable color mode. Defaults to False.
      force_terminal:
        Enable/disable terminal control codes, or None to auto-detect terminal. Defaults to None.
      debug:
        Enable/disable debugging information to be print printed to `file_stderr`.
    """

    global console_stderr
    global console_stdout
    global debug_on

    # https://rich.readthedocs.io/en/stable/console.html#file-output
    # Don't limit the output to console width. Rich console doesn't allow to set unlimited
    # terminal width, so set it here to large enough size, that could be considered
    # as unlimited.
    width = 10000
    console_stderr = Console(file=file_stderr, stderr=True, width=width, quiet=quiet, no_color=no_color,
                             force_terminal=force_terminal)
    console_stdout = Console(file=file_stdout, width=width, quiet=quiet, no_color=no_color, force_terminal=force_terminal)

    debug_on = debug
