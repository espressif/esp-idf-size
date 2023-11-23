# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from argparse import Namespace
from typing import Any, Dict

from rich.tree import Tree

from . import log
from .format_table import color_diff, color_size


def show(memmap: Dict[str, Any], args: Namespace) -> None:

    tree = Tree('Memory Types')
    for mem_type_name, mem_type_info in memmap['memory_types'].items():
        size = color_size(mem_type_info['size'], mem_type_info['size_diff'], args.diff)
        used = color_diff(mem_type_info['used'], mem_type_info['used_diff'], args.diff)
        mem_type_tree = tree.add(f'{mem_type_name} {used} / {size}',
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
