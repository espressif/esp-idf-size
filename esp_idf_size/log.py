# SPDX-FileCopyrightText: 2023-2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

"""Basic logging functions utilizing esp_pylib."""

__all__ = ['err', 'warn', 'die', 'debug', 'eprint', 'print']

import sys
from typing import Any, Optional

from esp_pylib.logger import log


def err(*args: Any, suggestion: Optional[str] = None) -> None:
    log.err(*args, suggestion=suggestion)


def warn(*args: Any, suggestion: Optional[str] = None) -> None:
    log.warn(*args, suggestion=suggestion)


def die(*args: Any, exit_code: int = 1, suggestion: Optional[str] = None) -> None:
    log.die(*args, exit_code=exit_code, suggestion=suggestion)


def debug(*args: Any) -> None:
    log.debug(*args)


def eprint(*args: Any, **kwargs: Any) -> None:
    log.print(*args, file=sys.stderr, **kwargs)


def print(*args: Any, **kwargs: Any) -> None:
    log.print(*args, **kwargs)
