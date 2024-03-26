import json
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

import pytest
import utils


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption('--url',
                     default='https://github.com/espressif/esp-idf-size-test.git',
                     metavar='URL',
                     help='git URL from which the build artifacts should be fetched')


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

    artifacts_path = tmp_dir_path / 'test_memmap'
    targets = utils.targets()

    # Fix project_path and build_dir paths in project_description json files so they point
    # to the cloned directory. Artifacts stored within the esp-idf-size-test repo have directories
    # from where they were generated, which does not match the checkout directory for testing.
    for target in targets:
        target_path = artifacts_path / target
        proj_desc_path = target_path / 'project_description.json'
        with open(proj_desc_path) as f:
            proj_desc = json.load(f)

        proj_desc['project_path'] = str(target_path)
        proj_desc['build_dir'] = str(target_path)

        with open(proj_desc_path, 'w') as f:
            json.dump(proj_desc, f, indent=4)

    return tmp_dir_path
