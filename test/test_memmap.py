# SPDX-FileCopyrightText: 2023-2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import sys
from distutils.dir_util import copy_tree
from pathlib import Path
from subprocess import PIPE, run
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import pytest

from esp_idf_size import memorymap
from esp_idf_size.elf import STT_FUNC, STT_NOTYPE

sys.path.append(str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402


@pytest.mark.parametrize('target', utils.targets())
def test_memmap(target: str, artifacts: Path) -> None:
    # Generate new memory map based on target artifacts and compare it
    # with the reference memory map.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    # Get the project name from the project_description to identify the map file name.
    with open(artifacts / 'test_memmap' / target / 'project_description.json') as f:
        proj_desc = json.load(f)

    map_fn = os.path.join(proj_desc['build_dir'], proj_desc['project_name'] + '.map')

    # Generate memory map and compare it with the reference one
    run(
        [sys.executable, '-m', 'esp_idf_size', '--format', 'raw', '-o', 'memmap.json', map_fn],
        cwd=tmp_dir_path,
        check=True,
    )

    with open(artifacts / 'test_memmap' / target / 'memmap.json') as f:
        memmap_ref = json.load(f)

    with open(tmp_dir_path / 'memmap.json') as f:
        memmap_new = json.load(f)

    # Fix project_path in the reference memory map. The rest of it should
    # match newly generated memory map.
    memmap_ref['project_path'] = memmap_new['project_path']

    assert memmap_ref == memmap_new


@pytest.mark.parametrize('proj_desc_state', ['missing', 'mismatched'])
def test_memmap_elf_next_to_map(proj_desc_state: str, artifacts: Path) -> None:
    # The ELF file name is normally taken from project_description.json. If the
    # project description is not available for the map file, the ELF file located
    # next to the map file under the same name has to be used. The memory map must
    # be the same as the reference one, which was generated with the project
    # description.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    # Directory with artifacts for the esp32 target
    artifacts_dir = artifacts / 'test_memmap' / 'esp32'

    with open(artifacts_dir / 'project_description.json') as f:
        proj_desc = json.load(f)

    # Copy only the map file and the ELF file, so the project description from
    # the artifacts directory is not found next to the map file.
    map_fn = proj_desc['project_name'] + '.map'
    shutil.copy(artifacts_dir / map_fn, tmp_dir_path)
    shutil.copy(artifacts_dir / proj_desc['app_elf'], tmp_dir_path)

    if proj_desc_state == 'mismatched':
        # The project description describes another executable of the project,
        # so it is ignored for the tested map file.
        proj_desc['app_elf'] = 'other.elf'
        with open(tmp_dir_path / 'project_description.json', 'w') as f:
            json.dump(proj_desc, f)

    run(
        [sys.executable, '-m', 'esp_idf_size', '--format', 'raw', '-o', 'memmap.json', map_fn],
        cwd=tmp_dir_path,
        check=True,
    )

    with open(artifacts_dir / 'memmap.json') as f:
        memmap_ref = json.load(f)

    with open(tmp_dir_path / 'memmap.json') as f:
        memmap_new = json.load(f)

    # Fix project_path in the reference memory map. The rest of it should
    # match newly generated memory map.
    memmap_ref['project_path'] = memmap_new['project_path']

    assert memmap_ref == memmap_new


@pytest.mark.parametrize('target_option', [True, False])
def test_memmap_target_option(target_option: bool, artifacts: Path) -> None:
    # The target is normally found in project_description.json or in the map
    # file. If it is in neither of them, as for a ULP binary, it has to be set
    # with the --target option.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    # Directory with artifacts for the esp32c6 target
    target = 'esp32c6'
    artifacts_dir = artifacts / 'test_memmap' / target

    with open(artifacts_dir / 'project_description.json') as f:
        proj_desc = json.load(f)

    # Copy only the ELF file, so the project description from the artifacts
    # directory is not found next to the map file.
    map_fn = proj_desc['project_name'] + '.map'
    shutil.copy(artifacts_dir / proj_desc['app_elf'], tmp_dir_path)

    # Create a map file without the target information. Rename the symbol and
    # the object file, which the map file parser uses to detect the target.
    map_text = (artifacts_dir / map_fn).read_text(encoding='utf-8')
    map_text = map_text.replace('IDF_TARGET_', 'XDF_TARGET_').replace('project_elf_src_', 'project_elf_xrc_')
    (tmp_dir_path / map_fn).write_text(map_text, encoding='utf-8')

    target_args = ['--target', target] if target_option else []

    p = run(
        [sys.executable, '-m', 'esp_idf_size', *target_args, '--format', 'raw', '-o', 'memmap.json', map_fn],
        cwd=tmp_dir_path,
        stderr=PIPE,
        text=True,
    )

    if not target_option:
        # There is no other source of the target
        assert p.returncode != 0
        assert 'cannot determine chip target' in p.stderr
        return

    assert p.returncode == 0, p.stderr
    # The target missing in the map file is not reported, because it was set with the option.
    assert 'cannot find target' not in p.stderr
    # No target was detected, so there is nothing to replace and to report.
    assert 'is replaced by the requested target' not in p.stderr

    with open(artifacts_dir / 'memmap.json') as f:
        memmap_ref = json.load(f)

    with open(tmp_dir_path / 'memmap.json') as f:
        memmap_new = json.load(f)

    # Fix project_path in the reference memory map. The rest of it should
    # match newly generated memory map.
    memmap_ref['project_path'] = memmap_new['project_path']

    assert memmap_ref == memmap_new

    # The target is used also for the map file specified with the --diff option.
    run(
        [
            sys.executable,
            '-m',
            'esp_idf_size',
            *target_args,
            '--diff',
            map_fn,
            '--format',
            'raw',
            '-o',
            'memmap_diff.json',
            map_fn,
        ],
        cwd=tmp_dir_path,
        check=True,
    )

    with open(tmp_dir_path / 'memmap_diff.json') as f:
        memmap_diff = json.load(f)

    assert memmap_diff['target'] == target
    assert memmap_diff['target_diff'] == target


def test_memmap_target_option_override(artifacts: Path) -> None:
    # The target set with the --target option has priority over the detected
    # one. The detected target is replaced and a warning is printed.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    # Directory with artifacts for the esp32c6 target
    target = 'esp32c6'
    artifacts_dir = artifacts / 'test_memmap' / target

    with open(artifacts_dir / 'project_description.json') as f:
        proj_desc = json.load(f)

    map_fn = os.path.join(proj_desc['build_dir'], proj_desc['project_name'] + '.map')

    requested_target = 'esp32c5'

    p = run(
        [
            sys.executable,
            '-m',
            'esp_idf_size',
            '--target',
            requested_target,
            '--format',
            'raw',
            '-o',
            'memmap.json',
            map_fn,
        ],
        cwd=tmp_dir_path,
        stderr=PIPE,
        text=True,
    )

    assert p.returncode == 0, p.stderr
    assert f'The chip target {target} detected for' in p.stderr
    assert f'is replaced by the requested target {requested_target}' in p.stderr

    with open(tmp_dir_path / 'memmap.json') as f:
        memmap = json.load(f)

    assert memmap['target'] == requested_target

    # No warning is printed if the requested target is the same as the detected one.
    p = run(
        [sys.executable, '-m', 'esp_idf_size', '--target', target, '--format', 'raw', '-o', 'memmap.json', map_fn],
        cwd=tmp_dir_path,
        stderr=PIPE,
        text=True,
    )

    assert p.returncode == 0, p.stderr
    assert 'is replaced by the requested target' not in p.stderr


# Minimal map file of a ULP binary. The ULP coprocessor accesses its memory
# from address 0x0, so the memory region and the sections start there.
ULP_MAP = """\
Memory Configuration

Name             Origin             Length             Attributes
ram              0x00000000         0x00001000         rw
*default*        0x00000000         0xffffffff

Linker script and memory map

.text           0x00000000       0x80
 *(.text)
 .text          0x00000000       0x80 CMakeFiles/ulp_main.dir/start.S.obj
                0x00000000                __start

.bss            0x00000080        0x4
 *(.bss)
 .bss           0x00000080        0x4 CMakeFiles/ulp_main.dir/main.c.obj

OUTPUT(ulp_main.elf elf32-littleriscv)
"""


@pytest.mark.parametrize('target', ['esp32', 'esp32s2', 'esp32s3'])
def test_memmap_ulp_address(target: str) -> None:
    # The ULP FSM and ULP RISC-V coprocessors access the RTC slow memory from
    # address 0x0, while the main CPU accesses it from address 0x50000000. The
    # memory region at address 0x0 in the map file of a ULP binary has to be
    # assigned to the RTC SLOW memory type.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    (tmp_dir_path / 'ulp_main.map').write_text(ULP_MAP)

    # The map file of a ULP binary does not contain the target, so it is set with the option.
    run(
        [
            sys.executable,
            '-m',
            'esp_idf_size',
            '--target',
            target,
            '--format',
            'json2',
            '-o',
            'summary.json',
            'ulp_main.map',
        ],
        cwd=tmp_dir_path,
        check=True,
    )

    with open(tmp_dir_path / 'summary.json') as f:
        summary = json.load(f)

    assert summary['layout'] == [
        {
            'name': 'RTC SLOW',
            'total': 0x1000,
            'used': 0x84,
            'free': 0x1000 - 0x84,
            'parts': {
                '.text': {'size': 0x80},
                '.bss': {'size': 0x4},
            },
        }
    ]


@pytest.mark.parametrize('target', ['esp32s2', 'esp32s3'])
def test_memmap_target_from_peripherals(target: str) -> None:
    # The map file of a ULP RISC-V or LP core binary does not contain the
    # IDF_TARGET symbol, but ESP-IDF passes the peripherals linker script of
    # the target to the link and the map file lists it. The target has to be
    # detected from its name, so the --target option is not needed.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    load_line = f'LOAD /esp-idf/components/ulp/subproject/components/ulp_riscv/ld/{target}.peripherals.ld\n'
    map_text = ULP_MAP.replace('Linker script and memory map\n\n', 'Linker script and memory map\n\n' + load_line)
    assert load_line in map_text
    (tmp_dir_path / 'ulp_main.map').write_text(map_text)

    run(
        [sys.executable, '-m', 'esp_idf_size', '--format', 'raw', '-o', 'memmap.json', 'ulp_main.map'],
        cwd=tmp_dir_path,
        check=True,
    )

    with open(tmp_dir_path / 'memmap.json') as f:
        memmap = json.load(f)

    assert memmap['target'] == target
    assert {name: (info['used'], info['size']) for name, info in memmap['memory_types'].items() if info['used']} == {
        'RTC SLOW': (0x84, 0x1000)
    }


# Map file of a ULP FSM binary. The binary file starts with a header and the
# sections are stored after it, so the linker reports a load address for them.
ULP_FSM_MAP = """\
Memory Configuration

Name             Origin             Length             Attributes
ram              0x0000000000000000 0x0000000000000400 rw
*default*        0x0000000000000000 0xffffffffffffffff

Linker script and memory map


.text           0x0000000000000000       0xd4 load address 0x000000000000000c
 *(.text)
 .text          0x0000000000000000       0xb8 CMakeFiles/ulp_main.dir/pulse_cnt.ulp.S.obj
                0x0000000000000000                entry
 .text          0x00000000000000b8       0x1c CMakeFiles/ulp_main.dir/wake_up.ulp.S.obj
                0x00000000000000b8                wake_up

.data           0x00000000000000d4        0x0 load address 0x00000000000000e0
                0x00000000000000d4                . = ALIGN (0x4)
 *(.data)
 .data          0x00000000000000d4        0x0 CMakeFiles/ulp_main.dir/pulse_cnt.ulp.S.obj
 .data          0x00000000000000d4        0x0 CMakeFiles/ulp_main.dir/wake_up.ulp.S.obj

.bss            0x00000000000000d4       0x18 load address 0x00000000000000e0
                0x00000000000000d4                . = ALIGN (0x4)
 *(.bss)
 .bss           0x00000000000000d4       0x18 CMakeFiles/ulp_main.dir/pulse_cnt.ulp.S.obj
                0x00000000000000d4                next_edge
 .bss           0x00000000000000ec        0x0 CMakeFiles/ulp_main.dir/wake_up.ulp.S.obj

.header         0x00000000000000ec        0xc load address 0x0000000000000000
                0x00000000000000ec        0x4 LONG 0x706c75
                0x00000000000000f0        0x2 SHORT 0xc LOADADDR (.text)
                0x00000000000000f2        0x2 SHORT 0xd4 SIZEOF (.text)
                0x00000000000000f4        0x2 SHORT 0x0 SIZEOF (.data)
                0x00000000000000f6        0x2 SHORT 0x18 SIZEOF (.bss)
LOAD CMakeFiles/ulp_main.dir/pulse_cnt.ulp.S.obj
LOAD CMakeFiles/ulp_main.dir/wake_up.ulp.S.obj
OUTPUT(ulp_main.elf elf32-esp32ulp)
"""


def test_memmap_ulp_fsm() -> None:
    # The map file of a ULP FSM binary has a load address for each output
    # section. The sections have to be reported with the size and at the
    # address, at which they are running.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)

    (tmp_dir_path / 'ulp_main.map').write_text(ULP_FSM_MAP)

    # The map file of a ULP binary does not contain the target, so it is set with the option.
    run(
        [
            sys.executable,
            '-m',
            'esp_idf_size',
            '--target',
            'esp32',
            '--format',
            'json2',
            '-o',
            'summary.json',
            'ulp_main.map',
        ],
        cwd=tmp_dir_path,
        check=True,
    )

    with open(tmp_dir_path / 'summary.json') as f:
        summary = json.load(f)

    # The .header section is not reported. It is only the header of the binary
    # file, which is not loaded into the RTC slow memory.
    assert summary['layout'] == [
        {
            'name': 'RTC SLOW',
            'total': 0x400,
            'used': 0xD4 + 0x18,
            'free': 0x400 - 0xD4 - 0x18,
            'parts': {
                '.text': {'size': 0xD4},
                '.bss': {'size': 0x18},
            },
        }
    ]


@pytest.mark.parametrize('elf_symbol', [True, False])
def test_memmap_input_section_symbols(elf_symbol: bool) -> None:
    # An input section without any ELF symbol is used as a symbol itself, so
    # the symbols of an object file add up to its size. This has to work also
    # for an input section located after the last ELF symbol and for an ELF
    # file without any usable symbol, e.g. the ELF file of a ULP FSM binary,
    # which is written in assembly.
    input_sections = [
        {'name': '.text.first', 'address': 0x00, 'size': 0x10},
        {'name': '.text.func', 'address': 0x10, 'size': 0x20},
        {'name': '.text.last', 'address': 0x30, 'size': 0x08},
    ]

    if elf_symbol:
        symbols = [SimpleNamespace(name='func', type=STT_FUNC, st_value=0x10, st_size=0x20)]
    else:
        # Label in assembly, which has no type and no size
        symbols = [SimpleNamespace(name='func', type=STT_NOTYPE, st_value=0x10, st_size=0)]

    memorymap._add_symbols_to_sections(SimpleNamespace(symbols=symbols), [{'input_sections': input_sections}])

    assert [input_section['symbols'] for input_section in input_sections] == [
        [{'name': '.text.first', 'address': 0x00, 'size': 0x10}],
        [{'name': 'func()' if elf_symbol else '.text.func', 'address': 0x10, 'size': 0x20}],
        [{'name': '.text.last', 'address': 0x30, 'size': 0x08}],
    ]


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        prog='test_memmap',
        description=(
            "Generate project's reference artifacts for specified targets. "
            'These artifacts are used for the memory map testing.'
        ),
    )

    parser.add_argument(
        '-p',
        '--project',
        metavar='PROJECT_PATH',
        default=os.path.join(os.environ.get('IDF_PATH', ''), 'examples', 'get-started', 'hello_world'),
        help=('Path to the reference project, which artifacts will be generated. Default is hello_world.'),
    )
    parser.add_argument(
        '-o',
        '--output-directory',
        metavar='OUTPUT_DIRECTORY',
        default='artifacts',
        help=(
            'Output directory where the generated artifacts will be stored. '
            'It will contain subdirectory for each target. Default is artifacts.'
        ),
    )
    parser.add_argument(
        'targets',
        metavar='TARGET',
        nargs='*',
        default=utils.targets(),
        help=('Targets for which artifacts will be generated. Default is all targets.'),
    )

    args = parser.parse_args()

    if not os.environ.get('IDF_PATH'):
        sys.exit('error: ESP-IDF environment is not set.')

    unknown_targets = ', '.join(set(args.targets) - set(utils.targets()))
    if unknown_targets:
        sys.exit(f'error: unknown targets: {unknown_targets}')

    IDF_PY_PATH = Path(os.environ['IDF_PATH']) / 'tools' / 'idf.py'
    tmpdir = TemporaryDirectory()
    project_path = Path(args.project)
    copy_tree(str(project_path), tmpdir.name, verbose=0)
    project_path = Path(tmpdir.name)

    for target in args.targets:
        outdir = Path(args.output_directory).resolve() / target
        outdir.mkdir(parents=True, exist_ok=True)

        run([sys.executable, IDF_PY_PATH, '--preview', 'set-target', target], cwd=project_path, check=True)
        run([sys.executable, IDF_PY_PATH, 'app'], cwd=project_path, check=True)

        with open(project_path / 'build' / 'project_description.json') as f:
            proj_desc = json.load(f)

        map_file = str(project_path / 'build' / (proj_desc['project_name'] + '.map'))

        run(
            [sys.executable, '-m', 'esp_idf_size', '--format', 'raw', '-o', str(outdir / 'memmap.json'), map_file],
            cwd=project_path,
            check=True,
        )

        shutil.copy(project_path / 'build' / proj_desc['app_elf'], outdir)
        shutil.copy(project_path / 'build' / map_file, outdir)
        shutil.copy(project_path / 'build' / 'project_description.json', outdir)

        # Generate output format artifacts
        run(
            [sys.executable, '-m', 'esp_idf_size', '--format', 'table', '-o', str(outdir / 'summary.table'), map_file],
            cwd=project_path,
            check=True,
        )

        run(
            [
                sys.executable,
                '-m',
                'esp_idf_size',
                '--format',
                'table',
                '--archives',
                '-o',
                str(outdir / 'archives.table'),
                map_file,
            ],
            cwd=project_path,
            check=True,
        )

        run(
            [
                sys.executable,
                '-m',
                'esp_idf_size',
                '--format',
                'table',
                '--files',
                '-o',
                str(outdir / 'files.table'),
                map_file,
            ],
            cwd=project_path,
            check=True,
        )

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
                str(outdir / 'archive_details.table'),
                map_file,
            ],
            cwd=project_path,
            check=True,
        )
