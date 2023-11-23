# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
from argparse import Namespace
from typing import Any, Dict

from . import log, memorymap


def show_summary(memmap: Dict[str, Any], args: Namespace) -> None:
    summary: Dict[str, Any] = {
        'version': '1.0',
        'layout': [],
    }

    for mem_type_name, mem_type_info in memmap['memory_types'].items():
        mem_type = {
            'name': mem_type_name,
            'total': mem_type_info['size'],
            'used': mem_type_info['used'],
            'free': mem_type_info['size'] - mem_type_info['used'],
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
    log.print(json.dumps(summary, indent=4))


def show_archives(memmap: Dict[str, Any], args: Namespace) -> None:
    summary = memorymap.get_archives_summary(memmap, args)
    log.print(json.dumps(summary, indent=4))


def show_symbols(memmap: Dict[str, Any], args: Namespace) -> None:
    summary = memorymap.get_symbols_summary(memmap, args)
    log.print(json.dumps(summary, indent=4))


def show(memmap: Dict[str, Any], args: Namespace) -> None:
    if args.archives:
        show_archives(memmap, args)
    elif args.archive_details:
        show_symbols(memmap, args)
    elif args.files:
        show_object_files(memmap, args)
    else:
        show_summary(memmap, args)
