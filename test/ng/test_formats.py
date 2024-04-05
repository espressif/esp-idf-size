# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import filecmp
import json
import os
import sys
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

import pytest
import utils


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

    run([sys.executable, '-m', 'esp_idf_size', '--ng', '--format', 'table', '-o', 'summary.table', map_fn],
        cwd=tmp_dir_path, check=True)
    assert filecmp.cmp(artifacts_dir / 'summary.table', tmp_dir_path / 'summary.table', shallow=False)

    run([sys.executable, '-m', 'esp_idf_size', '--ng', '--format', 'table', '--archives', '-o', 'archives.table', map_fn],
        cwd=tmp_dir_path, check=True)
    assert filecmp.cmp(artifacts_dir / 'archives.table', tmp_dir_path / 'archives.table', shallow=False)

    run([sys.executable, '-m', 'esp_idf_size', '--ng', '--format', 'table', '--files', '-o', 'files.table', map_fn],
        cwd=tmp_dir_path, check=True)
    assert filecmp.cmp(artifacts_dir / 'files.table', tmp_dir_path / 'files.table', shallow=False)

    run([sys.executable, '-m', 'esp_idf_size', '--ng', '--format', 'table', '--archive-details',
         'libesp_system.a', '-o', 'archive_details.table', map_fn], cwd=tmp_dir_path, check=True)
    assert filecmp.cmp(artifacts_dir / 'archive_details.table', tmp_dir_path / 'archive_details.table', shallow=False)
