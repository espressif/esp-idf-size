# SPDX-FileCopyrightText: 2023-2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from argparse import Namespace
from typing import Any, Dict, Optional

from rich.tree import Tree

from . import deps, log, mapfile, memorymap
from .elf import Elf
from .format_table import color_diff, color_size


def show_memmap(memmap: Dict[str, Any], args: Namespace) -> None:

    memorymap.trim(memmap, args)
    memorymap.sort(memmap, args)

    tree = Tree('Memory Types')
    for mem_type_name, mem_type_info in memmap['memory_types'].items():
        used = color_diff(mem_type_info['used'], mem_type_info['used_diff'], args.diff)
        if mem_type_info['size']:
            size = color_size(mem_type_info['size'], mem_type_info['size_diff'], args.diff)
            mem_type_tree = tree.add(f'{mem_type_name} {used} / {size}',
                                     style='dark_orange', guide_style='dark_orange')
        else:
            mem_type_tree = tree.add(f'{mem_type_name} {used}',
                                     style='dark_orange', guide_style='dark_orange')

        for section_name, section_info in mem_type_info['sections'].items():
            name = section_info['abbrev_name'] if args.abbrev else section_name
            size = color_diff(section_info['size'], section_info['size_diff'], args.diff)
            section_tree = mem_type_tree.add(f'{name} {size}', style='bright_blue', guide_style='bright_blue')

            for archive_name, archive_info in section_info['archives'].items():
                name = archive_info['abbrev_name'] if args.abbrev else archive_name
                size = color_diff(archive_info['size'], archive_info['size_diff'], args.diff)
                archive_tree = section_tree.add(f'{name} {size}', style='green', guide_style='green')

                for object_file_name, object_file_info in archive_info['object_files'].items():
                    name = object_file_info['abbrev_name'] if args.abbrev else object_file_name
                    size = color_diff(object_file_info['size'], object_file_info['size_diff'], args.diff)
                    symbol_tree = archive_tree.add(f'{name} {size}', style='default', guide_style='default')

                    for symbol_name, symbol_info in object_file_info['symbols'].items():
                        name = symbol_name
                        size = color_diff(symbol_info['size'], symbol_info['size_diff'], args.diff)
                        symbol_tree.add(f'{name} {size}', style='default', guide_style='default')

    log.print(tree)


def show_archives_dependencies(memmap: Dict[str, Any], map_file: mapfile.MapFile, elf: Optional[Elf], args: Namespace) -> None:
    arch_deps = deps.get_archives_dependencies(map_file, memmap, elf, args)
    if args.dep_reverse:
        tree_name = 'Archive reverse dependencies'
    else:
        tree_name = 'Archive dependencies'

    tree = Tree(tree_name)

    for arch_name, arch_info in arch_deps.items():
        arch_name_abbrev = arch_info['abbrev_name'] if args.abbrev else arch_name
        arch_size = arch_info['size']
        arch_tree = tree.add(f'{arch_name_abbrev} {arch_size}', style='dark_orange', guide_style='dark_orange')

        for arch_dep_name, arch_dep_info in arch_info['archives'].items():
            arch_dep_name_abbrev = arch_dep_info['abbrev_name'] if args.abbrev else arch_dep_name
            arch_dep_size = arch_dep_info['size']
            dep_tree = arch_tree.add(f'{arch_dep_name_abbrev} {arch_dep_size}', style='bright_blue', guide_style='bright_blue')

            if args.dep_symbols:
                for sym in arch_dep_info['symbols']:
                    dep_tree.add(sym, style='default', guide_style='default')

    log.print(tree)


def show(memmap: Dict[str, Any], map_file: mapfile.MapFile, elf: Optional[Elf], args: Namespace) -> None:
    if args.archive_dependencies:
        show_archives_dependencies(memmap, map_file, elf, args)
    else:
        show_memmap(memmap, args)
