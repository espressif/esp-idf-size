#!/usr/bin/env python
# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

class ARTIFACTS:
    MAPFILE = 'mapfile.map'
    BOOTLOADER_MAPFILE = 'bootloader.map'
    MAPFILE_REF = 'mapfile_ref.map'
    SUMMARY = 'summary'
    BOOTLOADER_SUMMARY = 'bootloader_summary'
    SUMMARY_DIFF = 'summary_diff'
    SUMMARY_DIFF_REV = 'summary_diff_rev'
    ARCHIVES = 'archives'
    ARCHIVES_DIFF = 'archives_diff'
    ARCHIVES_DIFF_REV = 'archives_diff_rev'
    ARCHIVE_DETAILS = 'archive_details'
    ARCHIVE_DETAILS_FILE = 'libmain.a'
    ARCHIVE_DETAILS_DIFF = 'archive_details_diff'
    ARCHIVE_DETAILS_DIFF_REV = 'archive_details_diff_rev'
    FILES = 'files'
    FILES_DIFF = 'files_diff'
    FILES_DIFF_REV = 'files_diff_rev'


if __name__ == '__main__':

    import argparse
    import json
    import os
    import shutil
    import sys
    from pathlib import Path
    from subprocess import run
    from tempfile import TemporaryDirectory
    from typing import List, Optional

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    import utils

    if not os.environ.get('IDF_PATH'):
        sys.exit('error: ESP-IDF environment is not set.')

    parser = argparse.ArgumentParser(
        prog='generate_artifacts.py',
        description=('Generate project\'s reference artifacts for specified targets. '
                     'These artifacts are used for the memory map testing.'))

    parser.add_argument('-p', '--project',
                        metavar='PROJECT_PATH',
                        default=os.path.join(os.environ.get('IDF_PATH', ''),
                                             'examples', 'get-started', 'hello_world'),
                        help=('Path to the project, which artifacts will be generated. '
                              'Default is hello_world.'))
    parser.add_argument('-r', '--reference',
                        metavar='PROJECT_PATH',
                        default=os.path.join(os.environ.get('IDF_PATH', ''),
                                             'examples', 'get-started', 'blink'),
                        help=('Path to the reference project, which artifacts will used for diff comparison. '
                              'Default is blink.'))
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

    unknown_targets = ', '.join(set(args.targets) - set(utils.targets()))
    if unknown_targets:
        sys.exit(f'error: uknown targets: {unknown_targets}')

    IDF_PATH = Path(os.environ['IDF_PATH'])
    IDF_PY_PATH = IDF_PATH / 'tools' / 'idf.py'
    TMPDIR = TemporaryDirectory()
    PROJECT_PATH = Path(TMPDIR.name) / 'project'
    REFERENCE_PROJECT_PATH = Path(TMPDIR.name) / 'reference_project'

    shutil.copytree(args.project, PROJECT_PATH)
    shutil.copytree(args.reference, REFERENCE_PROJECT_PATH)

    for target in args.targets:
        outdir = Path(args.output_directory).resolve() / target
        outdir.mkdir(parents=True, exist_ok=True)
        mapfile_out = str(outdir / ARTIFACTS.MAPFILE)
        mapfile_ref_out = str(outdir / ARTIFACTS.MAPFILE_REF)

        # build projects and store link map files
        for proj_path, map_dst in [(PROJECT_PATH, mapfile_out), (REFERENCE_PROJECT_PATH, mapfile_ref_out)]:
            run([sys.executable, IDF_PY_PATH, '--preview', 'set-target', target], cwd=proj_path, check=True)
            run([sys.executable, IDF_PY_PATH, 'build'], cwd=proj_path, check=True)
            with open(proj_path / 'build' / 'project_description.json') as f:
                proj_desc = json.load(f)

            map_src = str(proj_path / 'build' / (proj_desc['project_name'] + '.map'))
            shutil.copy(map_src, map_dst)

        # copy bootloader.map into target artifacts
        shutil.copy(str(PROJECT_PATH / 'build' / 'bootloader' / 'bootloader.map'), str(outdir / ARTIFACTS.BOOTLOADER_MAPFILE))

        def create_artifact(fmt: str,
                            basename: str,
                            report: Optional[List[str]],
                            mapfile: str,
                            mapfile_ref: Optional[str]) -> None:
            output_fn = f'{basename}.{fmt}'
            cmd = [sys.executable, '-m', 'esp_idf_size', '--format', fmt, '-o', str(output_fn)]
            if report is not None:
                cmd += report

            if mapfile_ref is not None:
                cmd += ['--diff', os.path.basename(mapfile_ref)]

            cmd += [os.path.basename(mapfile)]
            run(cmd, check=True, cwd=str(outdir))

        for fmt in ['text', 'csv', 'json']:
            # Summary
            create_artifact(fmt, ARTIFACTS.SUMMARY, None, mapfile_out, None)
            create_artifact(fmt, ARTIFACTS.SUMMARY_DIFF, None, mapfile_out, mapfile_ref_out)
            create_artifact(fmt, ARTIFACTS.SUMMARY_DIFF_REV, None, mapfile_ref_out, mapfile_out)

            # Archives
            create_artifact(fmt, ARTIFACTS.ARCHIVES, ['--archives'], mapfile_out, None)
            create_artifact(fmt, ARTIFACTS.ARCHIVES_DIFF, ['--archives'], mapfile_out, mapfile_ref_out)
            create_artifact(fmt, ARTIFACTS.ARCHIVES_DIFF_REV, ['--archives'], mapfile_ref_out, mapfile_out)

            # Archive details
            create_artifact(fmt, ARTIFACTS.ARCHIVE_DETAILS, ['--archive_details', ARTIFACTS.ARCHIVE_DETAILS_FILE],
                            mapfile_out, None)
            create_artifact(fmt, ARTIFACTS.ARCHIVE_DETAILS_DIFF, ['--archive_details', ARTIFACTS.ARCHIVE_DETAILS_FILE],
                            mapfile_out, mapfile_ref_out)
            create_artifact(fmt, ARTIFACTS.ARCHIVE_DETAILS_DIFF_REV, ['--archive_details', ARTIFACTS.ARCHIVE_DETAILS_FILE],
                            mapfile_ref_out, mapfile_out)

            # Files
            create_artifact(fmt, ARTIFACTS.FILES, ['--files'], mapfile_out, None)
            create_artifact(fmt, ARTIFACTS.FILES_DIFF, ['--files'], mapfile_out, mapfile_ref_out)
            create_artifact(fmt, ARTIFACTS.FILES_DIFF_REV, ['--files'], mapfile_ref_out, mapfile_out)

        # For bootloader generate basic summary report
        create_artifact('text', ARTIFACTS.BOOTLOADER_SUMMARY, None, str(outdir / ARTIFACTS.BOOTLOADER_MAPFILE), None)
