#!/usr/bin/env python

# SPDX-FileCopyrightText: 2023-2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import io
import locale
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import rich_click as click
from esp_pylib.excepthook import install_exception_reporting
from esp_pylib.logger import Verbosity
from esp_pylib.logger import log as esp_log

from . import format_csv, format_dot, format_json, format_raw, format_table, format_tree, log, mapfile, memorymap

install_exception_reporting()

# Show positional arguments in help (argparse default).
click.rich_click.SHOW_ARGUMENTS = True


def _show_doc() -> None:
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()
    readme_path = Path(os.path.realpath(os.path.dirname(__file__))) / 'docs' / 'readme.md'
    with open(readme_path) as fd:
        md = Markdown(fd.read())
    console.print(md)


def _doc_callback(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    _show_doc()
    ctx.exit()


def _filter_callback(_ctx: click.Context, _param: click.Parameter, value: Tuple[str, ...]) -> Optional[List[str]]:
    # The -F/--filter option uses multiple=True, so click yields a tuple of
    # patterns (an empty tuple when the option is not used). The rest of the
    # tool expects None for "no filtering" or a list of patterns, so normalize
    # the value here instead of in main().
    return list(value) if value else None


class _OutputBuffer(io.StringIO):
    # rich substitutes characters, which cannot be represented in the encoding
    # of the console file, with their ASCII counterparts. This applies e.g. to
    # box drawing characters. io.StringIO reports no encoding, in which case
    # rich assumes UTF-8. Report the encoding the buffer is written with by
    # _write_output_file(), so the report is rendered as if it was streamed
    # into the output file directly.
    encoding = locale.getpreferredencoding(False)


def _write_output_file(fn: str, data: str) -> None:
    try:
        path = Path(fn)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Escape characters, which cannot be represented in the output file
        # encoding, e.g. a symbol name with non-ASCII characters in a cp1252
        # locale, so a single symbol doesn't abort the whole report.
        path.write_text(data, encoding=_OutputBuffer.encoding, errors='backslashreplace')
    except OSError as e:
        log.die(f'cannot write to "{fn}": {e}')


def _run(args: Dict[str, Any]) -> None:
    # The report is rendered into a buffer and the output file is written only
    # after everything succeeded. Creating the file upfront would leave an empty
    # file behind on failure and, worse, destroy the output of a previous run.
    # Note that the file cannot be opened just before the output is generated
    # either, because the formatters may fail in the middle of rendering.
    ofile = _OutputBuffer() if args['output_file'] else None
    try:
        if ofile is not None:
            args['force_terminal'] = False

        esp_log.set_verbosity(
            Verbosity.SILENT if args['quiet'] else (Verbosity.VERBOSE if args['debug'] else Verbosity.NORMAL)
        )
        # width=10000 keeps wide tables/trees from being wrapped; highlight
        # matches the previous behaviour. emoji is disabled by esp_pylib by default.
        esp_log.set_console_options(
            file=ofile,
            no_color=args['no_color'],
            force_terminal=args['force_terminal'],
            width=10000,
            highlight=True,
            quiet=args['quiet'],
        )

        if args['no_abbrev'] and args['unify']:
            # --no-abbrev used along with --unify doesn't make sense, because
            # all entries(sections, archives, ...) are using already abbreviated names
            args['no_abbrev'] = False
            log.warn('The "--no-abbrev" option cannot be used with the "--unify" option and will be ignored.')

        if args['archive_dependencies'] and args['diff']:
            # --archive-dependencies rely on a cross-reference table, so it cannot be used with the --diff option.
            args['diff'] = None
            log.warn('The "--diff" option cannot be used with the "--archive-dependencies" option and will be ignored.')

        args['abbrev'] = not args['no_abbrev']

        load_symbols = args['archive_details'] or args['format'] == 'raw'

        if args['use_dwarf']:
            # We need DWARF only for detailed outputs like archives
            args['use_dwarf'] = any((args['archive_details'], args['archives'], args['files'], args['format'] == 'raw'))

        map_file = mapfile.MapFile(args['input_file'])
        elf = memorymap.get_elf(args['input_file'])
        memmap = memorymap.get(args['input_file'], load_symbols, args['use_dwarf'], map_file, elf)
        if not args['show_unused']:
            memorymap.remove_unused(memmap)
        if not args['use_flash_size']:
            memorymap.ignore_flash_size(memmap)
        if args['diff']:
            memmap_ref = memorymap.get(args['diff'], load_symbols, args['use_dwarf'])
            if not args['show_unused']:
                memorymap.remove_unused(memmap_ref)
            if not args['use_flash_size']:
                memorymap.ignore_flash_size(memmap)
            memmap = memorymap.diff(memmap, memmap_ref)
            if memmap['target'] != memmap['target_diff']:
                log.warn(
                    f'The target of the reference and other project is '
                    f'{memmap["target"]} and {memmap["target_diff"]}, respectively.'
                )

        if args['unify']:
            memorymap.unify(memmap)

        if args['format'] in ['table', 'text']:
            format_table.show(memmap, map_file, elf, args)
        elif args['format'] == 'json2':
            format_json.show(memmap, map_file, elf, args)
        elif args['format'] == 'raw':
            format_raw.show(memmap, map_file, elf, args)
        elif args['format'] == 'csv':
            format_csv.show(memmap, map_file, elf, args)
        elif args['format'] == 'tree':
            format_tree.show(memmap, map_file, elf, args)
        elif args['format'] == 'dot':
            format_dot.show(memmap, map_file, elf, args)

        if ofile is not None:
            # Reached only if the whole report was generated. Note that log.die
            # raises SystemExit, so it's not caught by the excepts below and
            # the output file is not written.
            _write_output_file(args['output_file'], ofile.getvalue())
    except (memorymap.MemMapException, mapfile.MapFileException) as e:
        log.die(str(e))
    except KeyboardInterrupt:
        sys.exit(1)


@click.command(
    context_settings={'help_option_names': ['-h', '--help']},
    help='This tool displays firmware size information for project built by ESP-IDF.',
)
@click.argument(
    'input_file', metavar='MAP_FILE', help='Path to the link map file generated by the ESP-IDF build system.'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'text', 'tree', 'csv', 'json2', 'raw', 'dot'], case_sensitive=False),
    default='table',
    show_default=True,
    help='Specify output format: table(text), tree, CSV, JSON, raw or DOT.',
)
@click.option('--archives', is_flag=True, help='Print per-archive sizes.')
@click.option(
    '--archive-dependencies',
    '--archive-deps',
    'archive_dependencies',
    is_flag=True,
    help='Display dependencies or reverse dependencies for all archives.',
)
@click.option(
    '--dep-symbols',
    '--dep-syms',
    'dep_symbols',
    is_flag=True,
    help='Include dependency symbols for the --archive-dependencies option.',
)
@click.option(
    '--dep-reverse',
    '--dep-rev',
    'dep_reverse',
    is_flag=True,
    help=(
        'Use reverse dependencies for the --archive-dependencies option. '
        'This will show the reverse dependencies of archives, instead '
        'of archives dependencies.'
    ),
)
@click.option(
    '--archive-details',
    '--archive_details',
    'archive_details',
    metavar='ARCHIVE_NAME',
    help='Print detailed symbols per archive.',
)
@click.option('--files', is_flag=True, help='Print per-file sizes.')
@click.option('--diff', metavar='MAP_FILE', help='Compare sizes with another project.')
@click.option('--no-abbrev', is_flag=True, help='Do not abbreviate section and file names.')
@click.option(
    '--unify',
    is_flag=True,
    help=(
        'Use abbreviated names with aggregated size information. '
        'For example .dram0.bss and .dram1.bss sections will be reported '
        'under one .bss section. Archives, object files and symbols will be '
        'aggregated too. This can be useful for the --diff option when '
        'comparing project built with different esp-idf versions.'
    ),
)
@click.option('--show-unused', is_flag=True, help='Show unused memory types and sections.')
@click.option('--show-unchanged', is_flag=True, help='Show unchanged items for --diff operation.')
@click.option(
    '--use-flash-size',
    is_flag=True,
    help=(
        'Show the total flash size as defined in the link map file. '
        'The actual flash size available for the application depends on factors such as the '
        'partition size for the application and other flash usage, so the total flash size '
        'in the link map file might not accurately represent the true available size.'
    ),
)
@click.option(
    '--lto/--no-lto',
    'use_dwarf',
    default=None,
    help=(
        'Enable or disable usage of DWARF debugging information to identify '
        'archives for symbols without archive. Intended to be used if LTO is enabled. '
        'If not specified, detect LTO usage from sdkconfig.json, if available.'
    ),
)
@click.option('-d', '--debug', is_flag=True, help='Print debug information. Messages are printed to stdout.')
@click.option(
    '-o', '--output-file', metavar='OUTPUT_FILE', help='Print output to the specified file instead of stdout.'
)
@click.option(
    '-s',
    '--sort',
    metavar='COLUMN',
    default='1',
    show_default=True,
    help=(
        'Sort table rows based on specified column number, starting from 0. '
        'Column can be specified also as negative number, where -1 means last column. '
        'Default is 1 and column 0, containing row description, cannot be used. '
        'The name of the column can be utilized in place of its numerical identifier. '
        'Applies only to table and CSV formats, except when --archive-dependencies '
        'is used; otherwise, it is ignored.'
    ),
)
@click.option(
    '-F',
    '--filter',
    'filter',
    metavar='PATTERN',
    multiple=True,
    callback=_filter_callback,
    help=(
        'Use the provided PATTERN to filter archives, object files, or '
        'symbols in table, CSV or DOT formats. The pattern can include wildcards: '
        '"*" - matches any sequence of characters, '
        '"?" - matches any single character, '
        '"[seq]" - matches any character in the sequence, '
        '"[!seq]" - matches any character not in the sequence. '
        'This option can be used multiple times, functioning as a logical OR.'
    ),
)
@click.option('--sort-diff', is_flag=True, help='Sort entries based on diff value instead of size.')
@click.option(
    '--sort-reverse',
    is_flag=True,
    default=True,
    flag_value=False,
    help='Sort entries in reversed order. By default descending order is used.',
)
@click.option('-q', '--quiet', is_flag=True, help='Suppress all output.')
@click.option('--no-color', is_flag=True, help='Disable ANSI color escape sequences.')
@click.option(
    '--force-terminal',
    is_flag=True,
    default=bool(os.environ.get('ESP_IDF_SIZE_FORCE_TERMINAL')) or None,
    help=(
        'Enable terminal control codes even if out is not attached to terminal. '
        'This option is ignored if used along with the "--output-file" option.'
    ),
)
@click.option(
    '--doc',
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_doc_callback,
    help='Display more comprehensive documentation.',
)
def main(**kwargs: Any) -> None:
    _run(kwargs)


if __name__ == '__main__':
    main()
