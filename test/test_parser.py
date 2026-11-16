# SPDX-FileCopyrightText: 2023-2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from esp_idf_size import mapfile


def test_parser(artifacts: Path) -> None:
    # Test that each link map file stored in artifacts repo
    # under the test_parser directory can be properly parsed.
    for entry in (artifacts / 'test_parser').rglob('*.map'):
        logging.info(f'Testing: {entry}')
        map_file = mapfile.MapFile(str(entry))
        map_file.validate()


# Map file with output sections, which are loaded at a different address than
# the one they are running at. The linker reports the load address for them.
LOAD_ADDRESS_MAP = """\
Memory Configuration

Name             Origin             Length             Attributes
ram              0x00000000         0x00000400         rw
*default*        0x00000000         0xffffffff

Linker script and memory map

.text           0x00000000       0xd4 load address 0x0000000c
 *(.text)
 .text          0x00000000       0xd4 CMakeFiles/ulp_main.dir/pulse_cnt.ulp.S.obj

.long_section_name.data
                0x000000d4        0x8 load address 0x000000e0
 *(.data)
 .data          0x000000d4        0x8 CMakeFiles/ulp_main.dir/pulse_cnt.ulp.S.obj

OUTPUT(ulp_main.elf elf32-esp32ulp)
"""


def test_parser_load_address() -> None:
    # The load address of an output section has to be accepted in both forms.
    # It is on the same line as the section name, or on the next line along
    # with the address and size, which the linker does for long section names.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    map_fn = Path(tmp_dir.name) / 'ulp_main.map'
    map_fn.write_text(LOAD_ADDRESS_MAP)

    map_file = mapfile.MapFile(str(map_fn))
    map_file.validate()

    sections = [(section['name'], section['address'], section['size']) for section in map_file.sections]
    assert sections == [
        ('.text', 0x0, 0xD4),
        ('.long_section_name.data', 0xD4, 0x8),
    ]


# Map file of a ULP binary without the IDF_TARGET symbol. The {lines} are
# replaced with the LOAD line of the peripherals linker script and other lines
# at the beginning of the "Linker script and memory map" part.
PERIPHERALS_MAP = """\
Memory Configuration

Name             Origin             Length             Attributes
ram              0x00000000         0x00001000         rw
*default*        0x00000000         0xffffffff

Linker script and memory map

{lines}
                0x60000000                        PROVIDE (UART0 = 0x60000000)

.text           0x00000000       0x80
 *(.text)
 .text          0x00000000       0x80 CMakeFiles/ulp_main.dir/start.S.obj

OUTPUT(ulp_main.elf elf32-littleriscv)
"""


@pytest.mark.parametrize(
    'lines,target',
    [
        # LP core binary
        ('LOAD /esp-idf/components/soc/esp32c6/ld/esp32c6.peripherals.ld', 'esp32c6'),
        # ULP RISC-V binary
        ('LOAD /esp-idf/components/ulp/subproject/components/ulp_riscv/ld/esp32s3.peripherals.ld', 'esp32s3'),
        # Path with backslashes
        ('LOAD C:\\esp-idf\\components\\soc\\esp32c5\\ld\\esp32c5.peripherals.ld', 'esp32c5'),
        # ULP FSM binary, which has no peripherals linker script
        ('LOAD CMakeFiles/ulp_main.dir/main.ulp.S.obj', ''),
        # The IDF_TARGET symbol has priority, even if it comes after the LOAD line
        (
            'LOAD /esp-idf/components/soc/esp32c6/ld/esp32c6.peripherals.ld\n'
            '                0x00000000                        IDF_TARGET_ESP32C5 = 0x0',
            'esp32c5',
        ),
    ],
)
def test_parser_target_from_peripherals(lines: str, target: str) -> None:
    # The map file of a ULP binary does not contain the IDF_TARGET symbol. If
    # the target is not found otherwise, it is taken from the name of the
    # peripherals linker script, which ESP-IDF passes to the LP core and ULP
    # RISC-V link.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    map_fn = Path(tmp_dir.name) / 'ulp_main.map'
    map_fn.write_text(PERIPHERALS_MAP.format(lines=lines))

    map_file = mapfile.MapFile(str(map_fn))

    assert map_file.target == target
