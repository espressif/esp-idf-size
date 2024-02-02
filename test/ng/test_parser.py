# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path
from subprocess import run


def test_parser(artifacts: Path) -> None:
    # Test that each link map file stored in artifacts repo
    # under the test_parser directory can be properly parsed.
    for entry in (artifacts / 'test_parser').rglob('*.map'):
        run([sys.executable, '-m', 'esp_idf_size', '--ng', entry], check=True)
