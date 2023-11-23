# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
from argparse import Namespace
from typing import Any, Dict

from . import log


def show(memmap: Dict[str, Any], args: Namespace) -> None:
    log.print(json.dumps(memmap, indent=4))
