# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from argparse import Namespace
from typing import Any, Dict

from rich.table import Table

from . import format_table, log


def show_table(table: Table) -> None:
    """Print Rich Table in CSV format"""

    # The plus one is for header cell
    matrix = [[''] * len(table.columns) for row in range(len(table.rows) + 1)]

    # Rich Table stores cells in columns so transform it to rows.
    for x, col in enumerate(table.columns):
        matrix[0][x] = f'"{col.header}"'
        for y, cell in enumerate(col.cells, start=1):
            cell = cell.strip()
            matrix[y][x] = f'"{cell}"'

    for row in matrix:
        log.print(','.join(row))


def show_summary(memmap: Dict[str, Any], args: Namespace) -> None:
    table = format_table.get_summary_table(memmap, args)
    show_table(table)


def show_object_files(memmap: Dict[str, Any], args: Namespace) -> None:
    table = format_table.get_object_files_table(memmap, args)
    show_table(table)


def show_archives(memmap: Dict[str, Any], args: Namespace) -> None:
    table = format_table.get_archives_table(memmap, args)
    show_table(table)


def show_symbols(memmap: Dict[str, Any], args: Namespace) -> None:
    table = format_table.get_symbols_table(memmap, args)
    show_table(table)


def show(memmap: Dict[str, Any], args: Namespace) -> None:
    if args.archives:
        show_archives(memmap, args)
    elif args.archive_details:
        show_symbols(memmap, args)
    elif args.files:
        show_object_files(memmap, args)
    else:
        show_summary(memmap, args)
