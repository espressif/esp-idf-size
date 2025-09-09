# SPDX-FileCopyrightText: 2023-2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
from argparse import Namespace
from typing import Any, Dict, Optional

from . import deps, log, mapfile, memorymap
from .elf import Elf


def show_summary(memmap: Dict[str, Any], args: Namespace) -> None:
    summary: Dict[str, Any] = {
        'version': '1.1',
        'layout': [],
    }

    memorymap.sort(memmap, args)

    for mem_type_name, mem_type_info in memmap['memory_types'].items():
        mem_type = {
            'name': mem_type_name,
            'total': mem_type_info['size'],
            'used': mem_type_info['used'],
            'free': mem_type_info['size'] - mem_type_info['used'] if mem_type_info['size'] else 0,
            'parts': {},
        }
        summary['layout'].append(mem_type)
        for section_name, section_info in mem_type_info['sections'].items():
            name = section_info['abbrev_name'] if args.abbrev else section_name
            mem_type['parts'][name] = {
                'size': section_info['size'],
            }

    log.print(json.dumps(summary, indent=4))


def show_object_files(memmap: Dict[str, Any], args: Namespace) -> None:
    summary = memorymap.get_object_files_summary(memmap, args)
    summary = memorymap.get_summary_sorted(summary, args)
    log.print(json.dumps(summary, indent=4))


def show_archives(memmap: Dict[str, Any], args: Namespace) -> None:
    summary = memorymap.get_archives_summary(memmap, args)
    summary = memorymap.get_summary_sorted(summary, args)
    log.print(json.dumps(summary, indent=4))


def show_symbols(memmap: Dict[str, Any], args: Namespace) -> None:
    summary = memorymap.get_symbols_summary(memmap, args)
    summary = memorymap.get_summary_sorted(summary, args)
    log.print(json.dumps(summary, indent=4))


def show_archives_dependencies(memmap: Dict[str, Any], map_file: mapfile.MapFile,
                               elf: Optional[Elf], args: Namespace) -> None:
    arch_deps = deps.get_archives_dependencies(map_file, memmap, elf, args)
    log.print(json.dumps(arch_deps, indent=4))


def show(memmap: Dict[str, Any], map_file: mapfile.MapFile, elf: Optional[Elf], args: Namespace) -> None:
    if args.archives:
        show_archives(memmap, args)
    elif args.archive_details:
        show_symbols(memmap, args)
    elif args.archive_dependencies:
        show_archives_dependencies(memmap, map_file, elf, args)
    elif args.files:
        show_object_files(memmap, args)
    else:
        show_summary(memmap, args)
