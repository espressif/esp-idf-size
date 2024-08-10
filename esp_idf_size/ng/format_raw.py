# SPDX-FileCopyrightText: 2023-2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
from argparse import Namespace
from typing import Any, Dict, Optional

from . import deps, log, mapfile
from .elf import Elf


def show(memmap: Dict[str, Any], map_file: mapfile.MapFile, elf: Optional[Elf], args: Namespace) -> None:
    if args.archive_dependencies:
        arch_deps = deps.get_archives_dependencies(map_file, memmap, elf, args)
        log.print(json.dumps(arch_deps, indent=4))
    else:
        log.print(json.dumps(memmap, indent=4))
