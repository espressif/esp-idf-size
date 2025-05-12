# SPDX-FileCopyrightText: 2023-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from argparse import Namespace
from collections import namedtuple
from typing import Any, Dict, List, Optional, Union

from rich.markup import escape
from rich.table import Table
from rich.text import Text

from . import deps, log, mapfile, memorymap
from .elf import Elf


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

    memorymap.trim(memmap, args)

    # Extend memory types and sections for percentage and remain info
    for mem_type_name, mem_type_info in memmap['memory_types'].items():
        if mem_type_info['size']:
            mem_type_info['pct'] = mem_type_info['used'] / mem_type_info['size'] * 100
            mem_type_info['remain'] = mem_type_info['size'] - mem_type_info['used']
        else:
            mem_type_info['pct'] = 0
            mem_type_info['remain'] = 0

        if mem_type_info['size'] - mem_type_info['size_diff']:
            mem_type_info['pct_diff'] = (mem_type_info['pct'] -
                                         ((mem_type_info['used'] - mem_type_info['used_diff']) /
                                          (mem_type_info['size'] - mem_type_info['size_diff']) * 100))
        else:
            mem_type_info['pct_diff'] = mem_type_info['pct'] - 0

        mem_type_info['remain_diff'] = mem_type_info['size_diff'] - mem_type_info['used_diff']
        mem_type_info['total'] = mem_type_info['size']
        mem_type_info['total_diff'] = mem_type_info['size_diff']

        for section_name, section_info in mem_type_info['sections'].items():
            if mem_type_info['size']:
                section_info['pct'] = section_info['size'] / mem_type_info['size'] * 100
            else:
                section_info['pct'] = 0

            if mem_type_info['size'] - mem_type_info['size_diff']:
                section_info['pct_diff'] = (section_info['pct'] -
                                            ((section_info['size'] - section_info['size_diff']) /
                                             (mem_type_info['size'] - mem_type_info['size_diff']) * 100))
            else:
                section_info['pct_diff'] = section_info['pct'] - 0

            # Add used/remain into section, so we can use the same sorting keys as for memory types.
            section_info['used'] = section_info['size']
            section_info['used_diff'] = section_info['size_diff']
            section_info['remain'] = 0
            section_info['remain_diff'] = 0
            section_info['total'] = 0
            section_info['total_diff'] = 0

    try:
        args.sort = int(args.sort)
    except ValueError:
        for idx, column in enumerate(table.columns):
            # We are using rich markup, which uses square brackets, in column header names, so
            # we need to covert them before comparison.
            if str(Text.from_markup(column.header)) == args.sort:
                args.sort = idx
                break
        else:
            log.die(f'Column "{escape(args.sort)}" not found')

    if args.sort == 0:
        log.die('Sorting based on column 0, which contains row description, is not supported.')

    try:
        sort_keys = ['used', 'pct', 'remain', 'total']
        sort_key = sort_keys[args.sort - 1 if args.sort > 0 else args.sort]
    except IndexError:
        log.die((f'Column index {args.sort} is out of range. '
                 f'Please use 1..{len(sort_keys)} or {-len(sort_keys)}..-1 range.'))

    if args.sort_diff:
        sort_key += '_diff'

    # Sort memory types first and later sections within them.
    mem_types_sorted = memorymap.sort_dict_by_key(memmap['memory_types'], sort_key, args.sort_reverse)

    for mem_type_name, mem_type_info in mem_types_sorted.items():
        if mem_type_info['size']:
            table.add_row(mem_type_name,
                          color_diff(mem_type_info['used'], mem_type_info['used_diff'], args.diff),
                          color_diff(round(mem_type_info['pct'], 2), round(mem_type_info['pct_diff'], 2), args.diff),
                          color_size(mem_type_info['remain'], mem_type_info['remain_diff'], args.diff),
                          color_size(mem_type_info['total'], mem_type_info['total_diff'], args.diff),
                          style='dark_orange')
        else:
            table.add_row(mem_type_name,
                          color_diff(mem_type_info['used'], mem_type_info['used_diff'], args.diff),
                          '',
                          '',
                          '',
                          style='dark_orange')

        sections_sorted = memorymap.sort_dict_by_key(mem_type_info['sections'], sort_key, args.sort_reverse)

        for section_name, section_info in sections_sorted.items():
            name = section_info['abbrev_name'] if args.abbrev else section_name

            if mem_type_info['size']:
                table.add_row(f'   {name}',
                              color_diff(section_info['used'], section_info['used_diff'], args.diff),
                              color_diff(round(section_info['pct'], 2), round(section_info['pct_diff'], 2), args.diff),
                              '',
                              '',
                              style='bright_blue')
            else:
                table.add_row(f'   {name}',
                              color_diff(section_info['used'], section_info['used_diff'], args.diff),
                              '',
                              '',
                              '',
                              style='bright_blue')

    return table


def _get_table_sorted(summary: Dict[str, Any], table: Table, args: Namespace) -> List[List[str]]:
    # Helper for get_*_table functions. It converts json summary into
    # table and sorts it.

    # Each column has three items:
    #   info - text representing the size, which is printed in the table
    #   size - used only for sorting purposes
    #   size_diff - used only for sorting purposes
    Column = namedtuple('Column', ['info', 'size', 'size_diff'])
    # Raw has name and list of Columns
    Row = namedtuple('Row', ['name', 'columns'])
    columns: List[Column] = []
    rows: List[Row] = []
    rows_final: List[List[str]] = []

    for entry_name, entry_info in summary.items():
        columns = []
        size = entry_info['size']
        diff = entry_info['size_diff']
        info = color_diff(size, diff, args.diff)
        columns.append(Column(info, size, diff))

        for mem_type_name, mem_type_info in entry_info['memory_types'].items():
            size = mem_type_info['size']
            diff = mem_type_info['size_diff']
            info = color_diff(size, diff, args.diff)
            columns.append(Column(info, size, diff))

            for section_name, section_info in mem_type_info['sections'].items():
                size = section_info['size']
                diff = section_info['size_diff']
                info = color_diff(size, diff, args.diff)
                columns.append(Column(info, size, diff))

        name = entry_info['abbrev_name'] if args.abbrev else entry_name
        rows.append(Row(name, columns))

    try:
        args.sort = int(args.sort)
    except ValueError:
        for idx, column in enumerate(table.columns):
            if column.header == args.sort:
                args.sort = idx
                break
        else:
            log.die(f'Column "{args.sort}" not found')

    if args.sort == 0:
        log.die('Sorting based on column 0, which contains row description, is not supported.')

    def sort_key(row: Row) -> int:
        sort_key_idx = args.sort - 1 if args.sort > 0 else args.sort

        if args.sort_diff:
            return int(row.columns[sort_key_idx].size_diff)
        else:
            return int(row.columns[sort_key_idx].size)

    try:
        rows = [row for row in sorted(rows, key=sort_key, reverse=args.sort_reverse)]
    except IndexError:
        log.die((f'Column index {args.sort} is out of range. '
                 f'Please use 1..{len(columns) - 1} or {-len(columns)}..-1 range.'))

    # Return only simple list of rows, where each row is a list
    # of columns to be printed in table.
    for row in rows:
        cols = [row.name] + [col.info for col in row.columns]
        rows_final.append(cols)

    return rows_final


def get_object_files_table(memmap: Dict[str, Any], args: Namespace) -> Table:
    object_files_summary = memorymap.get_object_files_summary(memmap, args)
    object_files_summary = memorymap.get_summary_filtered(object_files_summary, args)

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

    sizes_sorted = _get_table_sorted(object_files_summary, table, args)
    for sizes in sizes_sorted:
        table.add_row(*sizes)

    return table


def get_archives_table(memmap: Dict[str, Any], args: Namespace) -> Table:
    archives_summary = memorymap.get_archives_summary(memmap, args)
    archives_summary = memorymap.get_summary_filtered(archives_summary, args)

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

    sizes_sorted = _get_table_sorted(archives_summary, table, args)
    for sizes in sizes_sorted:
        table.add_row(*sizes)

    return table


def get_symbols_table(memmap: Dict[str, Any], args: Namespace) -> Table:
    symbols_summary = memorymap.get_symbols_summary(memmap, args)
    symbols_summary = memorymap.get_summary_filtered(symbols_summary, args)

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

    sizes_sorted = _get_table_sorted(symbols_summary, table, args)
    for sizes in sizes_sorted:
        table.add_row(*sizes)

    return table


def get_archives_dependencies_table(memmap: Dict[str, Any], map_file: mapfile.MapFile,
                                    elf: Optional[Elf], args: Namespace) -> Table:
    arch_deps = deps.get_archives_dependencies(map_file, memmap, elf, args)
    arch_deps = memorymap.get_summary_filtered(arch_deps, args)

    if args.dep_reverse:
        title = 'Table of reverse dependencies for archives'
        dep_col_name = 'Dependents'
    else:
        title = 'Table of dependencies for archives'
        dep_col_name = 'Dependencies'

    table = Table(title=title)
    table.add_column('Archive', overflow='fold', style='dark_orange3')
    table.add_column('Archive Size', overflow='fold')
    table.add_column(dep_col_name, overflow='fold', style='bright_blue')
    table.add_column(f'{dep_col_name} Sizes', overflow='fold')
    if args.dep_symbols:
        table.add_column('Symbols', overflow='fold')

    for arch_name, arch_info in arch_deps.items():
        arch_name_abbrev = arch_info['abbrev_name'] if args.abbrev else arch_name
        for cnt, arch_dep in enumerate(arch_info['archives'].items(), start=1):
            arch_dep_name, arch_dep_info = arch_dep
            arch_dep_name_abbrev = arch_dep_info['abbrev_name'] if args.abbrev else arch_dep_name
            if cnt == 1:
                row = [arch_name_abbrev, str(arch_info['size']), arch_dep_name_abbrev, str(arch_dep_info['size'])]
            else:
                row = ['', '', arch_dep_name_abbrev, str(arch_dep_info['size'])]

            if args.dep_symbols:
                row += ['\n'.join(arch_dep_info['symbols'])]
            if cnt == len(arch_info['archives']):
                table.add_row(*row, end_section=True)
            else:
                table.add_row(*row)

    return table


def show_summary(memmap: Dict[str, Any], args: Namespace) -> None:
    show_diff_info(memmap, args)
    table = get_summary_table(memmap, args)
    log.print(table)
    show_image_info(memmap, args)
    log.eprint(('[yellow]Note: The reported total sizes may be smaller than those '
                'in the technical reference manual due to reserved memory and application '
                'configuration. The total flash size available for the application is not '
                'included by default, as it cannot be reliably determined due to the presence '
                'of other data like the bootloader, partition table, and application partition size.'))


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


def show_archives_dependencies(memmap: Dict[str, Any], map_file: mapfile.MapFile,
                               elf: Optional[Elf], args: Namespace) -> None:
    table = get_archives_dependencies_table(memmap, map_file, elf, args)
    log.print(table)


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
