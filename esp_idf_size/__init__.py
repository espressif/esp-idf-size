# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

"""Package responsible for analyzing the binary size of firmware in ESP-IDF projects."""

__version__ = '2.0.0'

from . import log, memorymap

__all__ = [
    'memorymap',
    'log',
]
