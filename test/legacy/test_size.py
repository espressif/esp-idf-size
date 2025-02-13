# SPDX-FileCopyrightText: 2023-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from typing import List, Optional

import jsonschema
import pytest
from esptool.bin_image import LoadFirmwareImage
from generate_artifacts import ARTIFACTS as AF

sys.path.append(str(Path(__file__).resolve().parent.parent))
import utils  # noqa: E402


def cmp_files(file1: Path, file2: Path) -> None:
    """Compare two files regardless of their line endings."""
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        assert list(f1) == list(f2)


@pytest.mark.parametrize('target', utils.targets())
def test_outputs(target: str, artifacts_legacy: Path) -> None:
    # Compare with reference outputs produced by generate_artifacts.py.
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)
    artifacts_path = artifacts_legacy / target
    mapfile = str(artifacts_path / AF.MAPFILE)
    mapfile_ref = str(artifacts_path / AF.MAPFILE_REF)
    json_schema_path = Path(__file__).resolve().parent / 'size_schema.json'

    with open(json_schema_path, 'r') as schema_file:
        schema_json = json.load(schema_file)

    def cmp_outputs(fmt: str,
                    basename: str,
                    report: Optional[List[str]],
                    mapfile: str,
                    mapfile_diff: Optional[str]) -> None:
        output_fn = f'{basename}.{fmt}'
        cmd = [sys.executable, '-m', 'esp_idf_size', '--format', fmt, '-o', str(tmp_dir_path / output_fn)]
        if report is not None:
            cmd += report

        if mapfile_diff is not None:
            cmd += ['--diff', os.path.basename(mapfile_diff)]

        cmd += [os.path.basename(mapfile)]

        logging.info(f'Testing: {basename}.{fmt}')
        run(cmd, check=True, cwd=str(artifacts_path))

        cmp_files(artifacts_path / output_fn, tmp_dir_path / output_fn)

        if fmt == 'json':
            with open(tmp_dir_path / output_fn) as f:
                size_json = json.load(f)
            logging.info(f'Validating: {basename}.{fmt}')
            jsonschema.validate(size_json, schema_json)

    # Test app output formats
    for fmt in ['text', 'csv', 'json']:
        # Summary
        cmp_outputs(fmt, AF.SUMMARY, None, mapfile, None)
        cmp_outputs(fmt, AF.SUMMARY_DIFF, None, mapfile, mapfile_ref)
        cmp_outputs(fmt, AF.SUMMARY_DIFF_REV, None, mapfile_ref, mapfile)

        # Archives
        cmp_outputs(fmt, AF.ARCHIVES, ['--archives'], mapfile, None)
        cmp_outputs(fmt, AF.ARCHIVES_DIFF, ['--archives'], mapfile, mapfile_ref)
        cmp_outputs(fmt, AF.ARCHIVES_DIFF_REV, ['--archives'], mapfile_ref, mapfile)

        # Archive details
        cmp_outputs(fmt, AF.ARCHIVE_DETAILS, ['--archive_details', AF.ARCHIVE_DETAILS_FILE], mapfile, None)
        cmp_outputs(fmt, AF.ARCHIVE_DETAILS_DIFF, ['--archive_details', AF.ARCHIVE_DETAILS_FILE], mapfile, mapfile_ref)
        cmp_outputs(fmt, AF.ARCHIVE_DETAILS_DIFF_REV, ['--archive_details', AF.ARCHIVE_DETAILS_FILE], mapfile_ref, mapfile)

        # Files
        cmp_outputs(fmt, AF.FILES, ['--files'], mapfile, None)
        cmp_outputs(fmt, AF.FILES_DIFF, ['--files'], mapfile, mapfile_ref)
        cmp_outputs(fmt, AF.FILES_DIFF_REV, ['--files'], mapfile_ref, mapfile)

    # Test bootloader default summary output
    cmp_outputs('text', AF.BOOTLOADER_SUMMARY, None, str(artifacts_path / AF.BOOTLOADER_MAPFILE), None)


def test_misc_link_maps(artifacts_legacy: Path) -> None:
    # Test miscellaneous link maps, such as those with overflow.
    artifacts = artifacts_legacy / 'misc'
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)
    output_path = tmp_dir_path / 'output'

    for entry in artifacts.rglob('*.map'):
        logging.info(f'Testing: {entry}')
        cmd = [sys.executable, '-m', 'esp_idf_size', '-o', str(output_path), str(entry)]
        run(cmd, check=True)
        ref_path = entry.with_suffix(entry.suffix + '.out')
        cmp_files(output_path, ref_path)


@pytest.mark.parametrize('target', utils.targets())
def test_total_size(target: str) -> None:
    # Compare the overall size with the size reported by esptool.
    MAX_SIZE_DIFF = 100
    tmpdir = TemporaryDirectory()
    idf_path = Path(os.environ['IDF_PATH'])
    idf_py_path = idf_path / 'tools' / 'idf.py'
    tmpdir_path = Path(tmpdir.name) / 'project'
    hello_world_path = idf_path / 'examples' / 'get-started' / 'hello_world'
    size_json_path = tmpdir_path / 'size.json'
    mapfile_path = tmpdir_path / 'build' / 'hello_world.map'
    binfile_path = tmpdir_path / 'build' / 'hello_world.bin'

    shutil.copytree(str(hello_world_path), str(tmpdir_path))

    run([sys.executable, idf_py_path, '--preview', 'set-target', target], cwd=tmpdir_path, check=True)
    run([sys.executable, idf_py_path, 'build'], cwd=tmpdir_path, check=True)

    cmd = [sys.executable, '-m', 'esp_idf_size', '--format', 'json', '-o', str(size_json_path), str(mapfile_path)]
    run(cmd, cwd=tmpdir_path, check=True)

    with open(size_json_path, 'r') as f:
        data = json.load(f)
        size_total = data['total_size']

    esptool_total = 0
    img = LoadFirmwareImage(target, str(binfile_path))
    for seg in img.segments:
        seg_types = seg.get_memory_type(img)
        if 'PADDING' in seg_types:
            continue
        esptool_total += len(seg.data)

    logging.info((f'esp-idf-size total size: {size_total}, '
                  f'esptool total size: {esptool_total}, '
                  f'diff: {size_total - esptool_total}'))

    assert abs(size_total - esptool_total) <= MAX_SIZE_DIFF
