# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import sys
from distutils.dir_util import copy_tree
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from typing import Dict, Set

import pytest


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
    chip_info_dir = Path(__file__).parents[2] / 'esp_idf_size' / 'chip_info'
    targets = {f.with_suffix('').name for f in chip_info_dir.iterdir() if f.is_file() and f.suffix == '.yaml'}
    ctx['targets'] = targets - exclude
    return ctx['targets']


@pytest.fixture
def artifacts(pytestconfig: pytest.Config, ctx: dict={'tmpdir': None}) -> Path:
    # Download artifacts for testing into temporary directory and return
    # the directory path.
    if ctx['tmpdir']:
        return Path(ctx['tmpdir'].name)

    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)
    ctx['tmpdir'] = tmp_dir

    url = pytestconfig.getoption('url')
    run(['git', 'clone', '--quiet', '--depth', '1', '--single-branch', url, tmp_dir_path], check=True)

    return tmp_dir_path


@pytest.mark.parametrize('target', targets())
def test_memmap(target: str, artifacts: Path) -> None:
    # Generate new memory map based on target artifacts and compare it
    # with the reference memory map.

    # Temporary directory for testing
    tmp_dir = TemporaryDirectory()
    # The dirs_exist_ok arg for shutil.copytree was added in 3.8
    # so just append the test name as subdirectory to avoid getting
    # error that the dst directory already exists.
    tmp_dir_path = Path(tmp_dir.name) / 'test_memmap'

    # Build directory with reference artifacts for given target
    build_dir_path = Path(__file__).parent / artifacts / 'test_memmap' / target

    # Copy all artifacts for tested target into the temporary directory
    shutil.copytree(build_dir_path, tmp_dir_path)

    # Adjust project_path and build_dir to point to the temporary directory.
    with open(tmp_dir_path / 'project_description.json') as f:
        proj_desc = json.load(f)

    proj_desc['project_path'] = str(tmp_dir_path)
    proj_desc['build_dir'] = str(tmp_dir_path)

    with open(tmp_dir_path / 'project_description.json', 'w') as f:
        json.dump(proj_desc, f, indent=4)

    map_fn = os.path.join(proj_desc['build_dir'], proj_desc['project_name'] + '.map')

    # Generate new memory map based on the adjusted project_description.json
    run([sys.executable, '-m', 'esp_idf_size', '--ng', '--format', 'raw', '-o', 'memmap_new.json', map_fn],
        cwd=tmp_dir_path, check=True)

    with open(tmp_dir_path / 'memmap.json') as f:
        memmap_ref = json.load(f)

    with open(tmp_dir_path / 'memmap_new.json') as f:
        memmap_new = json.load(f)

    # Fix project_path in the reference memory map. The rest of it should
    # match newly generated memory map.
    memmap_ref['project_path'] = str(tmp_dir_path)

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
                        default=targets(),
                        help=('Targets for which artifacts will be generated. '
                              'Default is all targets.'))

    args = parser.parse_args()

    if not os.environ.get('IDF_PATH'):
        sys.exit('error: ESP-IDF environment is not set.')

    unknown_targets = ', '.join(set(args.targets) - set(targets()))
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
        run([sys.executable, '-m', 'esp_idf_size.ng', '--format', 'raw', '-o', str(outdir / 'memmap.json'),
             str(project_path / 'build' / 'project_description.json')],
            cwd=project_path, check=True)

        with open(project_path / 'build' / 'project_description.json') as f:
            proj_desc = json.load(f)

        shutil.copy(project_path / 'build' / proj_desc['app_elf'], outdir)
        shutil.copy(project_path / 'build' / (proj_desc['project_name'] + '.map'), outdir)
        shutil.copy(project_path / 'build' / 'project_description.json', outdir)
