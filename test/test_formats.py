# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import filecmp
import json
import logging
import os
import sys
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402


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

    logging.info(f'Testing: summary')
    run([sys.executable, '-m', 'esp_idf_size', '--format', 'table', '-o', 'summary.table', map_fn],
        cwd=tmp_dir_path, check=True)
    assert filecmp.cmp(artifacts_dir / 'summary.table', tmp_dir_path / 'summary.table', shallow=False)

    logging.info(f'Testing: archives')
    run([sys.executable, '-m', 'esp_idf_size', '--format', 'table', '--archives', '-o', 'archives.table', map_fn],
        cwd=tmp_dir_path, check=True)
    assert filecmp.cmp(artifacts_dir / 'archives.table', tmp_dir_path / 'archives.table', shallow=False)

    logging.info(f'Testing: files')
    run([sys.executable, '-m', 'esp_idf_size', '--format', 'table', '--files', '-o', 'files.table', map_fn],
        cwd=tmp_dir_path, check=True)
    assert filecmp.cmp(artifacts_dir / 'files.table', tmp_dir_path / 'files.table', shallow=False)

    logging.info(f'Testing: archive details')
    run([sys.executable, '-m', 'esp_idf_size', '--format', 'table', '--archive-details',
         'libesp_system.a', '-o', 'archive_details.table', map_fn], cwd=tmp_dir_path, check=True)
    assert filecmp.cmp(artifacts_dir / 'archive_details.table', tmp_dir_path / 'archive_details.table', shallow=False)
