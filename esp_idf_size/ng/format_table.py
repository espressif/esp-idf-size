# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from argparse import Namespace
from typing import Any, Dict, List, Union

from rich.table import Table

from . import log, memorymap


def show_diff_info(memmap: Dict[str, Any], args: Namespace) -> None:
    if not args.diff:
        return
    log.eprint('[bold]CURRENT[/]   project file: "{}"'.format(memmap['project_path']))
    log.eprint('[bold]REFERENCE[/] project file: "{}"'.format(memmap['project_path_diff']))
    log.eprint(('Difference is counted as [bold]CURRENT - REFERENCE[/], i.e. a positive '
                r'number means that [bold]CURRENT[/] is larger.'))


def show_image_info(memmap: Dict[str, Any], args: Namespace) -> None:
    msg = 'Total image size: {} bytes (.bin may be padded larger)'.format(
        color_diff(memmap['image_size'], memmap['image_size_diff'], args.diff))
    log.eprint(msg)


def color_diff(size: Union[int,float], size_diff: Union[int,float], diff: bool=False) -> str:
    # Color diff values. Red if bigger than zero.
    if not diff:
        return f'{size}'
    elif size_diff < 0:
        return f'{size}[green] {size_diff:+6}[/green]'
    elif size_diff > 0:
        return f'{size}[red] {size_diff:+6}[/red]'
    else:
        return f'{size} {size_diff:6}'


def color_size(size: Union[int,float], size_diff: Union[int,float], diff: bool=False) -> str:
    # Color size values. Red if less than zero.
    if not diff:
        return f'{size}'
    elif size_diff < 0:
        return f'{size}[red] {size_diff:+6}[/red]'
    elif size_diff > 0:
        return f'{size}[green] {size_diff:+6}[green]'
    else:
        return f'{size} {size_diff:6}'


def get_summary_table(memmap: Dict[str, Any], args: Namespace) -> Table:
    table = Table(title='Memory Type Usage Summary')
    table.add_column('Memory Type/Section', overflow='fold')
    table.add_column(r'Used \[bytes]', overflow='fold', justify='right')
    table.add_column(r'Used \[%]', overflow='fold', justify='right')
    table.add_column(r'Remain \[bytes]', overflow='fold', justify='right')
    table.add_column(r'Total \[bytes]', overflow='fold', justify='right')

    mem_type_sorted = {k: v for k, v in sorted(memmap['memory_types'].items(),
                                               key=lambda item: int(item[1]['used']),
                                               reverse=True)}

    for name, info in mem_type_sorted.items():
        if info['size']:
            pct = info['used'] / info['size'] * 100
        else:
            pct = 0
        if info['size'] - info['size_diff']:
            pct_diff = pct - ((info['used'] - info['used_diff']) / (info['size'] - info['size_diff']) * 100)
        else:
            pct_diff = pct - 0

        table.add_row(name,
                      color_diff(info['used'], info['used_diff'], args.diff),
                      color_diff(round(pct, 2), round(pct_diff, 2), args.diff),
                      color_size(info['size'] - info['used'], info['size_diff'] - info['used_diff'], args.diff),
                      color_size(info['size'], info['size_diff'], args.diff),
                      style='dark_orange')

        sections_sorted = {k: v for k, v in sorted(info['sections'].items(),
                                                   key=lambda item: int(item[1]['size']),
                                                   reverse=True)}

        for section_name, section_info in sections_sorted.items():
            name = section_info['abbrev_name'] if args.abbrev else section_name

            if info['size']:
                pct = section_info['size'] / info['size'] * 100
            else:
                pct = 0
            if info['size'] - info['size_diff']:
                pct_diff = pct - ((section_info['size'] - section_info['size_diff']) /
                                  (info['size'] - info['size_diff']) * 100)

            table.add_row(f'   {name}',
                          color_diff(section_info['size'], section_info['size_diff'], args.diff),
                          color_diff(round(pct, 2), round(pct_diff, 2), args.diff),
                          '',
                          '',
                          style='bright_blue')

    return table


def get_object_files_table(memmap: Dict[str, Any], args: Namespace) -> Table:
    object_files_summary = memorymap.get_object_files_summary(memmap, args)

    table = Table(title='Per-file contributions to ELF file')
    table.add_column('Object File', overflow='fold')
    table.add_column('Total Size', overflow='fold', justify='right')

    for object_file_name, object_file_info in object_files_summary.items():
        for mem_type_name, mem_type_info in object_file_info['memory_types'].items():
            table.add_column(mem_type_name, overflow='fold', justify='right', style='dark_orange')
            for section_name, section_info in mem_type_info['sections'].items():
                name = section_info['abbrev_name'] if args.abbrev else section_name
                table.add_column(name, overflow='fold', justify='right', style='bright_blue')
        break

    for object_file_name, object_file_info in object_files_summary.items():
        sizes: List[str] = []
        sizes.append(color_diff(object_file_info['size'], object_file_info['size_diff'], args.diff))
        for mem_type_name, mem_type_info in object_file_info['memory_types'].items():
            sizes.append(color_diff(mem_type_info['size'], mem_type_info['size_diff'], args.diff))
            for section_name, section_info in mem_type_info['sections'].items():
                sizes.append(color_diff(section_info['size'], section_info['size_diff'], args.diff))
        name = object_file_info['abbrev_name'] if args.abbrev else object_file_name
        table.add_row(name, *sizes)

    return table


def get_archives_table(memmap: Dict[str, Any], args: Namespace) -> Table:
    archives_summary = memorymap.get_archives_summary(memmap, args)

    table = Table(title='Per-archive contributions to ELF file')
    table.add_column('Archive File', overflow='fold')
    table.add_column('Total Size', overflow='fold', justify='right')

    for archive_name, archive_info in archives_summary.items():
        for mem_type_name, mem_type_info in archive_info['memory_types'].items():
            table.add_column(mem_type_name, overflow='fold', justify='right', style='dark_orange')
            for section_name, section_info in mem_type_info['sections'].items():
                name = section_info['abbrev_name'] if args.abbrev else section_name
                table.add_column(name, overflow='fold', justify='right', style='bright_blue')
        break

    for archive_name, archive_info in archives_summary.items():
        sizes: List[str] = []
        sizes.append(color_diff(archive_info['size'], archive_info['size_diff'], args.diff))
        for mem_type_name, mem_type_info in archive_info['memory_types'].items():
            sizes.append(color_diff(mem_type_info['size'], mem_type_info['size_diff'], args.diff))
            for section_name, section_info in mem_type_info['sections'].items():
                sizes.append(color_diff(section_info['size'], section_info['size_diff'], args.diff))
        name = archive_info['abbrev_name'] if args.abbrev else archive_name
        table.add_row(name, *sizes)

    return table


def get_symbols_table(memmap: Dict[str, Any], args: Namespace) -> Table:
    symbols_summary = memorymap.get_symbols_summary(memmap, args)

    table = Table(title=f'Symbols within archive: {args.archive_details} (Not all symbols may be reported)')
    table.add_column('Symbol', overflow='fold')
    table.add_column('Total Size', overflow='fold', justify='right')

    for symbol_name, symbol_info in symbols_summary.items():
        for mem_type_name, mem_type_info in symbol_info['memory_types'].items():
            table.add_column(mem_type_name, overflow='fold', justify='right', style='dark_orange')
            for section_name, section_info in mem_type_info['sections'].items():
                name = section_info['abbrev_name'] if args.abbrev else section_name
                table.add_column(name, overflow='fold', justify='right', style='bright_blue')
        break

    for symbol_name, symbol_info in symbols_summary.items():
        sizes: List[str] = []
        sizes.append(color_diff(symbol_info['size'], symbol_info['size_diff'], args.diff))
        for mem_type_name, mem_type_info in symbol_info['memory_types'].items():
            sizes.append(color_diff(mem_type_info['size'], mem_type_info['size_diff'], args.diff))
            for section_name, section_info in mem_type_info['sections'].items():
                sizes.append(color_diff(section_info['size'], section_info['size_diff'], args.diff))
        name = symbol_info['abbrev_name'] if args.abbrev else symbol_name
        table.add_row(name, *sizes)

    return table


def show_summary(memmap: Dict[str, Any], args: Namespace) -> None:
    show_diff_info(memmap, args)
    table = get_summary_table(memmap, args)
    log.print(table)
    show_image_info(memmap, args)


def show_archives(memmap: Dict[str, Any], args: Namespace) -> None:
    show_diff_info(memmap, args)
    table = get_archives_table(memmap, args)
    log.print(table)


def show_symbols(memmap: Dict[str, Any], args: Namespace) -> None:
    show_diff_info(memmap, args)
    table = get_symbols_table(memmap, args)
    log.print(table)


def show_object_files(memmap: Dict[str, Any], args: Namespace) -> None:
    show_diff_info(memmap, args)
    table = get_object_files_table(memmap, args)
    log.print(table)


def show(memmap: Dict[str, Any], args: Namespace) -> None:
    if args.archives:
        show_archives(memmap, args)
    elif args.archive_details:
        show_symbols(memmap, args)
    elif args.files:
        show_object_files(memmap, args)
    else:
        show_summary(memmap, args)
