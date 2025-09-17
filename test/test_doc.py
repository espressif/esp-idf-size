# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import sys
from subprocess import DEVNULL, run


def test_doc() -> None:
    run([sys.executable, '-m', 'esp_idf_size', '--doc'], stdout=DEVNULL, stderr=DEVNULL, check=True)
