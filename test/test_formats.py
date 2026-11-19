# SPDX-FileCopyrightText: 2024-2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import csv
import filecmp
import json
import logging
import os
import re
import sys
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402


@pytest.mark.parametrize('fmt', ['json2', 'table'])
def test_output_file_ansi_free(fmt: str, artifacts: Path) -> None:
    # The output file is a deliverable, which is often consumed by another tool,
    # e.g. idf-build-apps parses the json2 report, so it must never contain ANSI
    # escape sequences. Rich enables them for anything it considers a terminal
    # and the FORCE_COLOR environment variable, which is set e.g. in the esp-idf
    # CI, makes it consider one regardless of the actual output file.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    # Directory with artifacts for the esp32 target
    artifacts_dir = artifacts / 'test_memmap' / 'esp32'

    with open(artifacts_dir / 'project_description.json') as f:
        proj_desc = json.load(f)

    map_fn = os.path.join(artifacts_dir, proj_desc['project_name'] + '.map')

    run(
        [sys.executable, '-m', 'esp_idf_size', '--format', fmt, '-o', 'report', map_fn],
        cwd=tmp_dir_path,
        env={**os.environ, 'FORCE_COLOR': '1'},
        check=True,
    )

    report = (tmp_dir_path / 'report').read_text()
    assert '\x1b' not in report
    if fmt == 'json2':
        json.loads(report)


@pytest.mark.parametrize('unify', [False, True])
@pytest.mark.parametrize('map_name', ['bootloader.map', 'bootloader_esp32s2.map'])
def test_section_names_clash(map_name: str, unify: bool, artifacts: Path) -> None:
    # Several sections of one memory type may have the same abbreviated name.
    # The bootloader has the .iram.text and .iram_loader.text sections, which
    # are both abbreviated to .text. Such sections have to be reported under
    # their full names. Otherwise one would replace the other in the JSON
    # summary, where the section names are used as keys.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    map_fn = artifacts / 'test_parser' / 'legacy' / map_name

    run(
        [
            sys.executable,
            '-m',
            'esp_idf_size',
            '--format',
            'json2',
            *(['--unify'] if unify else []),
            '-o',
            'summary.json',
            map_fn,
        ],
        cwd=tmp_dir_path,
        check=True,
    )

    with open(tmp_dir_path / 'summary.json') as f:
        summary = json.load(f)

    section_names = set()
    for mem_type in summary['layout']:
        # No section is lost, so the section sizes add up to the used size.
        assert sum(part['size'] for part in mem_type['parts'].values()) == mem_type['used']
        section_names.update(mem_type['parts'])

    if unify:
        # The --unify option aggregates the sections with the same abbreviated name.
        assert '.text' in section_names
        assert not {'.iram.text', '.iram_loader.text'} & section_names
    else:
        # The sections with the same abbreviated name are reported under their full names.
        assert {'.iram.text', '.iram_loader.text'} <= section_names
    # The other sections keep their abbreviated names, e.g. .dram0.bss is reported as .bss.
    assert '.bss' in section_names
    assert '.dram0.bss' not in section_names


# Minimal map file of an LP core binary. The .vector.text and .text sections are
# both located in the LP RAM and both are abbreviated to .text. The target is
# given by the IDF_TARGET_ESP32C6 symbol, as in the map file of an application.
LP_CORE_MAP = """\
Memory Configuration

Name             Origin             Length             Attributes
vector_table     0x50000000         0x00000100         rwx
lp_ram           0x50000100         0x00003f00         rwx
*default*        0x00000000         0xffffffff

Linker script and memory map

                0x00000000                        IDF_TARGET_ESP32C6 = 0x0

.vector.text    0x50000000       {vector_size}
 *(.vector.text)
 .vector.text   0x50000000       {vector_size} CMakeFiles/ulp_main.dir/vector.S.obj
{text_section}
OUTPUT(ulp_main.elf elf32-littleriscv)
"""

LP_CORE_MAP_TEXT_SECTION = """
.text           0x50000100      0x100
 *(.text)
 .text          0x50000100      0x100 CMakeFiles/ulp_main.dir/main.c.obj
"""


def create_lp_core_build(build_dir_path: Path, vector_size: str = '0x80', text_section: bool = True) -> None:
    # Create a build directory with the map file of an LP core binary.
    build_dir_path.mkdir()
    (build_dir_path / 'ulp_main.map').write_text(
        LP_CORE_MAP.format(vector_size=vector_size, text_section=LP_CORE_MAP_TEXT_SECTION if text_section else '')
    )


@pytest.mark.parametrize('fmt', ['table', 'tree', 'csv'])
def test_section_names_clash_diff(fmt: str) -> None:
    # The sections with the same abbreviated name have to be reported under
    # their full names also with the --diff option, which does not show the
    # unchanged sections. Here the .vector.text section is bigger in the
    # current map file and the .text section is the same in both map files.
    # The .vector.text section must not be reported as .text, which is the
    # name of the other section.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    create_lp_core_build(tmp_dir_path / 'ref', vector_size='0x80')
    create_lp_core_build(tmp_dir_path / 'cur', vector_size='0x90')

    run(
        [
            sys.executable,
            '-m',
            'esp_idf_size',
            '--format',
            fmt,
            '--diff',
            'ref/ulp_main.map',
            '-o',
            'report',
            'cur/ulp_main.map',
        ],
        cwd=tmp_dir_path,
        check=True,
    )

    report = (tmp_dir_path / 'report').read_text()

    assert '.vector.text' in report
    # No section is reported as .text. The .text section itself is not changed,
    # so it is not shown.
    assert not re.search(r'(?<![\w.])\.text\b', report)


def test_section_names_clash_diff_reference_only() -> None:
    # The --diff option reports also the sections, which are only in the
    # reference map file. Such a section may have the same abbreviated name as
    # a section of the current map file. Here the .text section is only in the
    # reference map file, so .vector.text is the only section abbreviated to
    # .text in the current map file. Both sections still have to be reported
    # under their full names.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    create_lp_core_build(tmp_dir_path / 'ref')
    create_lp_core_build(tmp_dir_path / 'cur', text_section=False)

    run(
        [
            sys.executable,
            '-m',
            'esp_idf_size',
            '--format',
            'csv',
            '--diff',
            'ref/ulp_main.map',
            '--show-unchanged',
            '-o',
            'report',
            'cur/ulp_main.map',
        ],
        cwd=tmp_dir_path,
        check=True,
    )

    with open(tmp_dir_path / 'report', newline='') as f:
        names = [row[0] for row in csv.reader(f)]

    # The header, the memory type and its two sections
    assert names[:2] == ['Memory Type/Section', 'LP SRAM']
    assert sorted(names[2:]) == ['.text', '.vector.text']


@pytest.mark.parametrize('target', utils.targets())
def test_formats(target: str, artifacts: Path) -> None:
    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    # Directory with artifacts for given target
    artifacts_dir = artifacts / 'test_memmap' / target

    with open(artifacts_dir / 'project_description.json') as f:
        proj_desc = json.load(f)

    map_fn = os.path.join(artifacts_dir, proj_desc['project_name'] + '.map')

    logging.info('Testing: summary')
    run(
        [sys.executable, '-m', 'esp_idf_size', '--format', 'table', '-o', 'summary.table', map_fn],
        cwd=tmp_dir_path,
        check=True,
    )
    assert filecmp.cmp(artifacts_dir / 'summary.table', tmp_dir_path / 'summary.table', shallow=False)

    logging.info('Testing: archives')
    run(
        [sys.executable, '-m', 'esp_idf_size', '--format', 'table', '--archives', '-o', 'archives.table', map_fn],
        cwd=tmp_dir_path,
        check=True,
    )
    assert filecmp.cmp(artifacts_dir / 'archives.table', tmp_dir_path / 'archives.table', shallow=False)

    logging.info('Testing: files')
    run(
        [sys.executable, '-m', 'esp_idf_size', '--format', 'table', '--files', '-o', 'files.table', map_fn],
        cwd=tmp_dir_path,
        check=True,
    )
    assert filecmp.cmp(artifacts_dir / 'files.table', tmp_dir_path / 'files.table', shallow=False)

    logging.info('Testing: archive details')
    run(
        [
            sys.executable,
            '-m',
            'esp_idf_size',
            '--format',
            'table',
            '--archive-details',
            'libesp_system.a',
            '-o',
            'archive_details.table',
            map_fn,
        ],
        cwd=tmp_dir_path,
        check=True,
    )
    assert filecmp.cmp(artifacts_dir / 'archive_details.table', tmp_dir_path / 'archive_details.table', shallow=False)
