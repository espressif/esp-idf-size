# SPDX-FileCopyrightText: 2023-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import sys
from distutils.dir_util import copy_tree
from pathlib import Path
from subprocess import run
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
    run([sys.executable, '-m', 'esp_idf_size', '--format', 'raw', '-o', 'memmap.json', map_fn],
        cwd=tmp_dir_path, check=True)

    with open(artifacts / 'test_memmap' / target / 'memmap.json') as f:
        memmap_ref = json.load(f)

    with open(tmp_dir_path / 'memmap.json') as f:
        memmap_new = json.load(f)

    # Fix project_path in the reference memory map. The rest of it should
    # match newly generated memory map.
    memmap_ref['project_path'] = memmap_new['project_path']

    assert memmap_ref == memmap_new


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        prog='test_memmap',
        description=('Generate project\'s reference artifacts for specified targets. '
                     'These artifacts are used for the memory map testing.'))

    parser.add_argument('-p', '--project',
                        metavar='PROJECT_PATH',
                        default=os.path.join(os.environ.get('IDF_PATH', ''),
                                             'examples', 'get-started', 'hello_world'),
                        help=('Path to the reference project, which artifacts will be generated. '
                              'Default is hello_world.'))
    parser.add_argument('-o', '--output-directory',
                        metavar='OUTPUT_DIRECTORY',
                        default='artifacts',
                        help=('Output directory where the generated artifacts will be stored. '
                              'It will contains subdirectory for each target. Default is artifacts.'))
    parser.add_argument('targets',
                        metavar='TARGET',
                        nargs='*',
                        default=utils.targets(),
                        help=('Targets for which artifacts will be generated. '
                              'Default is all targets.'))

    args = parser.parse_args()

    if not os.environ.get('IDF_PATH'):
        sys.exit('error: ESP-IDF environment is not set.')

    unknown_targets = ', '.join(set(args.targets) - set(utils.targets()))
    if unknown_targets:
        sys.exit(f'error: uknown targets: {unknown_targets}')

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

        run([sys.executable, '-m', 'esp_idf_size', '--format', 'raw', '-o', str(outdir / 'memmap.json'),
             map_file],
            cwd=project_path, check=True)

        shutil.copy(project_path / 'build' / proj_desc['app_elf'], outdir)
        shutil.copy(project_path / 'build' / map_file, outdir)
        shutil.copy(project_path / 'build' / 'project_description.json', outdir)

        # Generate output format artifacts
        run([sys.executable, '-m', 'esp_idf_size', '--format', 'table', '-o', str(outdir / 'summary.table'),
             map_file],
            cwd=project_path, check=True)

        run([sys.executable, '-m', 'esp_idf_size', '--format', 'table',
             '--archives', '-o', str(outdir / 'archives.table'),
             map_file],
            cwd=project_path, check=True)

        run([sys.executable, '-m', 'esp_idf_size', '--format', 'table',
             '--files', '-o', str(outdir / 'files.table'),
             map_file],
            cwd=project_path, check=True)

        run([sys.executable, '-m', 'esp_idf_size', '--format', 'table',
             '--archive-details', 'libesp_system.a', '-o', str(outdir / 'archive_details.table'),
             map_file],
            cwd=project_path, check=True)
