# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from argparse import Namespace
from typing import Any, Dict, List, Optional

from . import deps, log, mapfile, memorymap
from .elf import Elf


def show_archives_dependencies(map_file: mapfile.MapFile, memmap: Dict[str, Any],
                               elf: Optional[Elf], args: Namespace) -> None:

    arch_deps = deps.get_archives_dependencies(map_file, memmap, elf, args)
    arch_deps = memorymap.get_summary_filtered(arch_deps, args)
    lines: List[str] = []
    seen: List[str] = []

    lines += ['strict digraph {']

    def add_node(name: str, name_abbrev: str, size: int) -> None:
        if name in seen:
            return
        shape = 'box' if name in arch_deps else 'ellipse'
        color = 'darkorange3' if name in arch_deps else 'azure'
        # Archive not previously seen, so add a node for it.
        lines.append(rf'"{name}" \[shape={shape}, label="{name_abbrev} ({size})", style=filled, fillcolor="{color}"]')
        seen.append(name)

    for arch_name, arch_info in arch_deps.items():
        arch_name_abbrev = arch_info['abbrev_name'] if args.abbrev else arch_name
        add_node(arch_name, arch_name_abbrev, arch_info['size'])

        for arch_dep_name, arch_dep_info in arch_info['archives'].items():
            arch_dep_name_abbrev = arch_dep_info['abbrev_name'] if args.abbrev else arch_dep_name
            add_node(arch_dep_name, arch_dep_name_abbrev, arch_dep_info['size'])

            if args.dep_reverse:
                line = f'"{arch_dep_name}" -> "{arch_name}"'
            else:
                line = f'"{arch_name}" -> "{arch_dep_name}"'
            if args.dep_symbols:
                syms_str = '\n'.join(arch_dep_info['symbols'])
                line += rf' \[label="{syms_str}"]'
            lines += [line]

    lines += ['}']

    log.print('\n'.join(lines))


def show(memmap: Dict[str, Any], map_file: mapfile.MapFile, elf: Optional[Elf], args: Namespace) -> None:
    if not args.archive_dependencies:
        log.die('The DOT output format is available only for the --archive-dependencies option.')
    show_archives_dependencies(map_file, memmap, elf, args)
