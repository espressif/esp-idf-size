from pytest import Parser


def pytest_addoption(parser: Parser) -> None:
    parser.addoption('--url',
                     default='https://github.com/espressif/esp-idf-size-test.git',
                     metavar='URL',
                     help='git URL from which the build artifacts should be fetched')
