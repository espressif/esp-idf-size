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

import pytest

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
