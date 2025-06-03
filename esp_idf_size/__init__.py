# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

"""Package responsible for analyzing the binary size of firmware in ESP-IDF projects."""

__version__ = '1.7.1'

from .ng import log, memorymap

__all__ = [
    'memorymap',
    'log',
]
