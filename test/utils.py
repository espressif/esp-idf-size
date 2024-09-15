# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

# Helper functions for testing

from pathlib import Path
from typing import Dict, Set


def targets(ctx: Dict[str,Set]={'targets': set()}) -> Set[str]:
    # Return set of targets found in the chip_info directory
    if ctx['targets']:
        return ctx['targets']

    # The esp32h4 chip is excluded, because it was renamed during development and
    # there is no support for this target in the idf.py. Since original and new esp-idf-size
    # implementations share the same chip info yaml files, we exclude it here, so we do
    # not break existing esp-idf-size implementation, which has support for this chip and
    # can be used by some users.
    # TODO: This should be excluded in the future once the new version replaces the current
    #       esp-idf-size implementation.
    exclude = {'esp32h4'}
    chip_info_dir = Path(__file__).parents[1] / 'esp_idf_size' / 'chip_info'
    targets = {f.with_suffix('').name for f in chip_info_dir.iterdir() if f.is_file() and f.suffix == '.yaml'}
    ctx['targets'] = targets - exclude
    return ctx['targets']
