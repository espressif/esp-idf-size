# SPDX-FileCopyrightText: 2023-2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import sys
from typing import IO, Any

from rich.console import Console

console_stderr = None
console_stdout = None
debug_on = False


def err(*args: Any) -> None:
    console_stderr.print('[red]error: ', *args)  # type: ignore


def warn(*args: Any) -> None:
    console_stderr.print('[yellow]warning: ', *args)  # type: ignore


def die(*args: Any) -> None:
    err(*args)
    sys.exit(1)


def debug(*args: Any) -> None:
    if debug_on:
        console_stderr.print('[bright_blue]debug: ', *args)  # type: ignore


def eprint(*args: Any) -> None:
    console_stderr.print(*args)  # type: ignore


def print(*args: Any) -> None:
    console_stdout.print(*args)  # type: ignore


def set_console(file: IO[str]=sys.stdout, quiet: bool=False, no_color: bool=False,
                force_terminal: bool=None, debug: bool=False) -> None:
    global console_stderr
    global console_stdout
    global debug_on

    # https://rich.readthedocs.io/en/stable/console.html#file-output
    # Don't limit the output to console width. Rich console doesn't allow to set unlimited
    # terminal width, so set it here to large enough size, that could be considered
    # as unlimited.
    width = 10000
    console_stderr = Console(stderr=True, width=width, quiet=quiet, no_color=no_color, force_terminal=force_terminal)
    console_stdout = Console(file=file, width=width, quiet=quiet, no_color=no_color, force_terminal=force_terminal)

    debug_on = debug
