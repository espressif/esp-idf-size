# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import os
from argparse import Namespace
from typing import Any, Dict, Optional

from . import log, mapfile, memorymap
from .elf import SHN_ABS, STT_FUNC, STT_OBJECT, Elf


def get_archives_deps(crt: Dict[str, Any], archives_sizes: Dict[str, Any]) -> Dict[str, Any]:
    # archives format:
    # {
    #     ref_archive: {
    #         abbrev_name:
    #         size:
    #         archives: {
    #             def_archive: {
    #                 abbrev_name:
    #                 size:
    #                 symbols: []
    #             }
    #         }
    #     }
    # }
    # where ref_archive is name of archive which uses symbols from def_archive(s)

    archives: Dict[str, Any] = {}

    for sym, refs in crt.items():
        def_archive = refs[0][0]
        ref_archives = {ref[0] for ref in refs[1:]}

        for ref_archive in ref_archives:
            if ref_archive not in archives:
                archives[ref_archive] = {
                    'abbrev_name': os.path.basename(ref_archive),
                    'size': archives_sizes[ref_archive]['size'],
                    'archives': {}
                }

            if def_archive not in archives[ref_archive]['archives']:
                archives[ref_archive]['archives'][def_archive] = {
                    'abbrev_name': os.path.basename(def_archive),
                    'size': archives_sizes[def_archive]['size'],
                    'symbols': []
                }

            archives[ref_archive]['archives'][def_archive]['symbols'].append(sym)

    return archives


def get_archives_revdeps(crt: Dict[str, Any], archives_sizes: Dict[str, Any]) -> Dict[str, Any]:
    # archives format:
    # {
    #     def_archive: {
    #         abbrev_name:
    #         size:
    #         archives: {
    #             ref_archive: {
    #                 abbrev_name:
    #                 size:
    #                 symbols: []
    #             }
    #         }
    #     }
    # }
    # where def_archive is name of archive where symbols used by ref_archive(s) are defined

    archives: Dict[str, Any] = {}

    for sym, refs in crt.items():
        def_archive = refs[0][0]
        ref_archives = {ref[0] for ref in refs[1:]}

        if def_archive not in archives:
            archives[def_archive] = {
                'abbrev_name': os.path.basename(def_archive),
                'size': archives_sizes[def_archive]['size'],
                'archives': {}
            }

        for ref_archive in ref_archives:
            if ref_archive not in archives[def_archive]['archives']:
                archives[def_archive]['archives'][ref_archive] = {
                    'abbrev_name': os.path.basename(ref_archive),
                    'size': archives_sizes[ref_archive]['size'],
                    'symbols': []
                }

            archives[def_archive]['archives'][ref_archive]['symbols'].append(sym)

    return archives


def _filter_crt(crt: Dict[str, Any], archives: Dict[str, Any], elf: Optional[Elf]) -> Dict[str, Any]:
    if elf:
        # Remove discarded symbols from the cross-reference table based on symbols in the ELF file.
        sym_names = [sym.name for sym in elf.symbols if sym.type in (STT_FUNC, STT_OBJECT) and sym.st_shndx != SHN_ABS]
        crt = {sym: refs for sym, refs in crt.items() if sym in sym_names}
    else:
        log.die('Displaying archives\' dependencies requires an ELF file to work properly.')

    # Remove archives that were not included in the ELF file based on the Linker script and memory map.
    # Additionally, eliminate the reference archive if it is identical to the definition archive.
    crt_filtered: Dict[str, Any] = {}
    for sym, refs in crt.items():
        def_archive = refs[0][0]
        if def_archive not in archives:
            continue

        refs_filtered = [(arch, obj) for arch, obj in refs[1:] if arch in archives and arch != def_archive]
        refs_filtered = [refs[0]] + refs_filtered
        if len(refs_filtered) > 1:
            # The symbol is used by at least one other archive.
            crt_filtered[sym] = refs_filtered

    return crt_filtered


def get_archives_dependencies(map_file: mapfile.MapFile, memmap: Dict[str, Any],
                              elf: Optional[Elf], args: Namespace) -> Dict[str, Any]:
    crt = map_file.cross_reference_table
    if crt is None:
        log.die('The cross-reference table is not available.')

    assert crt is not None  # help mypy

    archives = memorymap.get_archives_summary(memmap, args)

    crt = _filter_crt(crt, archives, elf)

    if args.dep_reverse:
        dependencies = get_archives_revdeps(crt, archives)
    else:
        dependencies = get_archives_deps(crt, archives)

    return dependencies
