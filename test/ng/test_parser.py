# SPDX-FileCopyrightText: 2023-2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from esp_idf_size.ng import mapfile


def test_parser(artifacts: Path) -> None:
    # Test that each link map file stored in artifacts repo
    # under the test_parser directory can be properly parsed.
    for entry in (artifacts / 'test_parser').rglob('*.map'):
        map_file = mapfile.MapFile(str(entry))
        map_file.validate()
