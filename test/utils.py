# SPDX-FileCopyrightText: 2024-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

# Helper functions for testing

from pathlib import Path
from typing import Dict, Set


def targets(ctx: Dict[str,Set]={'targets': set()}) -> Set[str]:
    # Return set of targets found in the chip_info directory
    if ctx['targets']:
        return ctx['targets']

    chip_info_dir = Path(__file__).parents[1] / 'esp_idf_size' / 'chip_info'
    targets = {f.with_suffix('').name for f in chip_info_dir.iterdir() if f.is_file() and f.suffix == '.yaml'}
    # The exclude set may be used if some targets should be excluded from testing.
    exclude: Set = set()
    ctx['targets'] = targets - exclude
    return ctx['targets']
