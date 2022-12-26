#!/usr/bin/env python
#
# SPDX-FileCopyrightText: 2018-2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from __future__ import print_function

import sys
from typing import Dict

try:
    import idf_size.core
except ImportError:
    sys.path.append('..')
    import idf_size.core


if __name__ == '__main__':
    # Should deliver a RuntimeError as the 'test' header doesn't exist
    try:
        idf_size.core.scan_to_header([], 'test')
    except RuntimeError as e:
        assert "Didn't find line" in str(e)

    # Should deliver a RuntimeError as there's no content under the heading
    try:
        idf_size.core.load_segments(['Memory Configuration'])
        pass
    except RuntimeError as e:
        assert 'End of file' in str(e)

    segments = {'iram0_0_seg': {'origin': 0, 'length': 0},
                'dram0_0_seg': {'origin': 0, 'length': 0}}
    sections = {}  # type: Dict

    print(idf_size.core.get_summary('a.map', segments, sections, 'esp32'), end='')
