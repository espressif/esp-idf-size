from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

import pytest


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

    return tmp_dir_path
