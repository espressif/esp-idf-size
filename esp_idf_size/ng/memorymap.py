# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import os
from argparse import Namespace
from typing import Any, Dict, Generator, List, Optional

import yaml
from elftools.common.exceptions import ELFError
from elftools.elf.constants import SH_FLAGS
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import Symbol

from . import log, mapfile


def get(input_fn: str, load_symbols: bool=False) -> Dict[str, Any]:
    """
    This is the main function, which returns a dictionary representing
    the whole memory map for a given project. It's converted by formatting
    functions to a requested format(table, json, cvs).

    Memory types are defined in chip info yaml files. These define the memory
    partitioning and all memory is divided into these memory types.

    Memory regions are defined in linker map file based on the MEMORY
    command in linker script. Memory regions are split according to the
    memory types. For example iram0_0_seg memory region for esp32s3 may span across
    multiple memory types defined in esp32s3.yaml(IRAM and DRAM_1). Such memory
    regions are split, so they fit into the defined memory types. This allows
    to correctly account memory usage for a specified memory type. Previously
    e.g. the total IRAM size included also DIRAM size.

    Output memory sections, here sometimes referred simply as sections, as loaded
    from linker's map file are split according to divided memory regions.

    Example:
    {
        'target': 'esp32s3',
        'target_diff': '',
        'image_size': 207313,
        'image_size_diff': 0,
        'project_path': '/home/fhrbata/work/esp-idf/examples/get-started/hello_world',
        'project_path_diff': '',
        'memory_types': {
            'IRAM': {
                'size': 16384,
                'size_diff': 0,
                'used': 16383,
                'used_diff': 0,
                'sections': {
                    '.iram0.text': {
                        'abbrev_name': '.text',
                        'size': 15356,
                        'size_diff': 0,
                        'archives': {
                            'esp-idf/esp_system/libesp_system.a': {
                                'abbrev_name': 'libesp_system.a',
                                'size': 3335,
                                'size_diff': 0,
                                'object_files': {
                                    'cpu_start.c.obj': {
                                        'abbrev_name': 'cpu_start.c.obj',
                                        'size': 1157,
                                        'size_diff': 0,
                                        'symbols': {
                                            '.iram1.0.literal': {
                                                'abbrev_name': '.iram1.0.literal',
                                                'size': 68,
                                                'size_diff': 0},


    The "*_diff" values contains zero by default, but when the current map is compared with other referenced
    map, these fields will contain current - referenced value.


    Some memory regions may map into the same memory. This is handled by comparing memory regions offsets with offsets
    specified in yaml files(primary and secondary address). For more information please see _get_mem_type_map().
    """

    memory_map: Dict[str, Any] = {
        'target': '',
        'target_diff': '',
        'image_size': 0,
        'image_size_diff': 0,
        'project_path': '',
        'project_path_diff': '',
        'memory_types': {},
    }

    proj_desc = elf_fn = map_fn = elf = target = None

    # Try to guess project description file path based on map file.
    proj_desc_fn = _get_project_description_fn(input_fn)

    # Load project description if available.
    proj_desc = _get_project_description(proj_desc_fn)

    if proj_desc:
        memory_map['project_path'] = proj_desc['project_path']
        target = proj_desc['target']
        elf_fn = os.path.join(proj_desc['build_dir'], proj_desc['app_elf'])
        map_fn = os.path.join(proj_desc['build_dir'], proj_desc['project_name'] + '.map')
    else:
        map_fn = input_fn

    if elf_fn:
        elf = _load_elf_file(elf_fn)
    else:
        log.debug(f'elf file is not available')

    # Parse linker map file memory regions, target and output sections
    map_file = mapfile.MapFile(map_fn)

    if not target:
        # Target from project_description.json is not available, use target detected in map file.
        target = map_file.target

    if not target:
        log.die(f'cannot determine chip target')

    memory_map['target'] = target

    # Get memory types from chip info yaml file
    memory_types = _get_memory_types(target)

    # Get ELF sections headers which form the app memory image
    elf_sections_headers = _get_elf_sections_headers(elf)

    # Filter memory regions and remove ones which are not interesting
    memory_regions_filtered = _filter_memory_regions(map_file.memory_regions)

    # Split memory regions into memory types if memory region covers/crosses more memory types
    # and assign each memory region a memory type.
    memory_regions_splitted = _split_memory_regions(memory_regions_filtered, memory_types)

    # Filter linker map output sections based on ELF section headers if available, otherwise
    # use output section names.
    map_sections_filtered = _filter_map_sections(map_file.sections, elf_sections_headers)

    # Get binary image size
    memory_map['image_size'] = _get_image_size(elf_sections_headers, map_sections_filtered)

    if load_symbols:
        # Add symbols from ELF file into filtered output sections
        _add_symbols_to_sections(elf, map_sections_filtered)
    else:
        # ELF symbols are not needed, so add empty symbols list for each input section
        for osec in map_sections_filtered:
            for isec in osec['input_sections']:
                isec['symbols'] = []

    # Split output sections according to splitted memory regions
    map_sections_splitted = _split_map_sections(map_sections_filtered, memory_regions_splitted)

    # Add archives info into sections. Archives contain objects and objects contains symbols.
    _add_archives_to_sections(map_sections_splitted)

    # Generate the overall memory map representation
    memory_map['memory_types'] = _get_mem_type_map(memory_types, memory_regions_splitted, map_sections_splitted)

    log.debug(f'memory map', memory_map)

    return memory_map


def diff(memory_map_cur: Dict[str, Any], memory_map_ref: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return memory map in the same format as the get() function, but all "*_diff" variables are
    properly filled with memory_map_cur - memory_map_ref value.

    This creates new memory_map_diff, which is a copy memory_map_cur. It's extended for
    entries, which are present in memory_map_ref only, so the memory_map_diff is a union of
    memory_map_cur and memory_map_ref. The memory_map_diff is walked through and all size and
    "*_diff" values are fixed.
    """
    memory_map_diff: Dict[str, Any]

    # Merge current memory map with referenced memory map into memory_map_diff, which
    # is based on the memory_map_cur.
    memory_map_diff = copy.deepcopy(memory_map_cur)

    memory_map_diff['target_diff'] = memory_map_ref['target']
    memory_map_diff['project_path_diff'] = memory_map_ref['project_path']
    memory_map_diff['image_size_diff'] = memory_map_cur['image_size'] - memory_map_ref['image_size']

    for mem_type_name_ref, mem_type_info_ref in memory_map_ref['memory_types'].items():
        if mem_type_name_ref not in memory_map_diff['memory_types']:
            memory_map_diff['memory_types'][mem_type_name_ref] = copy.deepcopy(mem_type_info_ref)
            continue

        sections_diff = memory_map_diff['memory_types'][mem_type_name_ref]['sections']

        for section_name_ref, section_info_ref in mem_type_info_ref['sections'].items():
            if section_name_ref not in sections_diff:
                sections_diff[section_name_ref] = copy.deepcopy(section_info_ref)
                continue

            archives_diff = sections_diff[section_name_ref]['archives']

            for archive_name_ref, archive_info_ref in section_info_ref['archives'].items():
                if archive_name_ref not in archives_diff:
                    archives_diff[archive_name_ref] = copy.deepcopy(archive_info_ref)
                    continue

                object_files_diff = archives_diff[archive_name_ref]['object_files']

                for object_file_name_ref, object_file_info_ref in archive_info_ref['object_files'].items():
                    if object_file_name_ref not in object_files_diff:
                        object_files_diff[object_file_name_ref] = copy.deepcopy(object_file_info_ref)
                        continue

                    symbols_diff = object_files_diff[object_file_name_ref]['symbols']

                    for symbol_name_ref, symbol_info_ref in object_file_info_ref['symbols'].items():
                        if symbol_name_ref not in symbols_diff:
                            symbols_diff[symbol_name_ref] = copy.deepcopy(symbol_info_ref)
                            continue

    # Fix sizes for items in ref, but not in cur and calculate diff sizes
    for mem_type_name_diff, mem_type_info_diff in memory_map_diff['memory_types'].items():
        mem_type_info_cur = memory_map_cur['memory_types'].get(mem_type_name_diff, {})
        mem_type_info_ref = memory_map_ref['memory_types'].get(mem_type_name_diff, {})
        if mem_type_info_cur and mem_type_info_ref:
            mem_type_info_diff['size_diff'] = mem_type_info_cur['size'] - mem_type_info_ref['size']
            mem_type_info_diff['used_diff'] = mem_type_info_cur['used'] - mem_type_info_ref['used']
        elif mem_type_info_cur:
            mem_type_info_diff['size_diff'] = mem_type_info_cur['size']
            mem_type_info_diff['used_diff'] = mem_type_info_cur['used']
        else:
            mem_type_info_diff['size'] = 0
            mem_type_info_diff['used'] = 0
            mem_type_info_diff['size_diff'] = 0 - mem_type_info_ref['size']
            mem_type_info_diff['used_diff'] = 0 - mem_type_info_ref['used']

        for section_name_diff, section_info_diff in mem_type_info_diff['sections'].items():
            section_info_cur = mem_type_info_cur.get('sections', {}).get(section_name_diff, {})
            section_info_ref = mem_type_info_ref.get('sections', {}).get(section_name_diff, {})
            if section_info_cur and section_info_ref:
                section_info_diff['size_diff'] = section_info_cur['size'] - section_info_ref['size']
            elif section_info_cur:
                section_info_diff['size_diff'] = section_info_cur['size']
            else:
                section_info_diff['size'] = 0
                section_info_diff['size_diff'] = 0 - section_info_ref['size']

            for archive_name_diff, archive_info_diff in section_info_diff['archives'].items():
                archive_info_cur = section_info_cur.get('archives', {}).get(archive_name_diff, {})
                archive_info_ref = section_info_ref.get('archives', {}).get(archive_name_diff, {})
                if archive_info_cur and archive_info_ref:
                    archive_info_diff['size_diff'] = archive_info_cur['size'] - archive_info_ref['size']
                elif archive_info_cur:
                    archive_info_diff['size_diff'] = archive_info_cur['size']
                else:
                    archive_info_diff['size'] = 0
                    archive_info_diff['size_diff'] = 0 - archive_info_ref['size']

                for obj_file_name_diff, obj_file_info_diff in archive_info_diff['object_files'].items():
                    obj_file_info_cur = archive_info_cur.get('object_files', {}).get(obj_file_name_diff, {})
                    obj_file_info_ref = archive_info_ref.get('object_files', {}).get(obj_file_name_diff, {})
                    if obj_file_info_cur and obj_file_info_ref:
                        obj_file_info_diff['size_diff'] = obj_file_info_cur['size'] - obj_file_info_ref['size']
                    elif obj_file_info_cur:
                        obj_file_info_diff['size_diff'] = obj_file_info_cur['size']
                    else:
                        obj_file_info_diff['size'] = 0
                        obj_file_info_diff['size_diff'] = 0 - obj_file_info_ref['size']

                    for symbol_name_diff, symbol_info_diff in obj_file_info_diff['symbols'].items():
                        symbol_info_cur = obj_file_info_cur.get('symbols', {}).get(symbol_name_diff, {})
                        symbol_info_ref = obj_file_info_ref.get('symbols', {}).get(symbol_name_diff, {})
                        if symbol_info_cur and symbol_info_ref:
                            symbol_info_diff['size_diff'] = symbol_info_cur['size'] - symbol_info_ref['size']
                        elif symbol_info_cur:
                            symbol_info_diff['size_diff'] = symbol_info_cur['size']
                        else:
                            symbol_info_diff['size'] = 0
                            symbol_info_diff['size_diff'] = 0 - symbol_info_ref['size']

    log.debug(f'memory map diff', memory_map_diff)
    return memory_map_diff


def walk(memory_map: Dict[str, Any], depth: str='all') -> Generator:
    """Generator which yields tuple for memory type tree entries."""
    for mem_type_name, mem_type_info in memory_map['memory_types'].items():
        if depth == 'types':
            yield (mem_type_name, mem_type_info,
                   None, None,
                   None, None,
                   None, None,
                   None, None)
            continue
        for section_name, section_info in mem_type_info['sections'].items():
            if depth == 'sections':
                yield (mem_type_name, mem_type_info,
                       section_name, section_info,
                       None, None,
                       None, None,
                       None, None)
                continue
            for archive_name, archive_info in section_info['archives'].items():
                if depth == 'archives':
                    yield (mem_type_name, mem_type_info,
                           section_name, section_info,
                           archive_name, archive_info,
                           None, None,
                           None, None)
                    continue
                for object_file_name, object_file_info in archive_info['object_files'].items():
                    if depth == 'objects':
                        yield (mem_type_name, mem_type_info,
                               section_name, section_info,
                               archive_name, archive_info,
                               object_file_name, object_file_info,
                               None, None)
                        continue
                    for symbol_name, symbol_info in object_file_info['symbols'].items():
                        yield (mem_type_name, mem_type_info,
                               section_name, section_info,
                               archive_name, archive_info,
                               object_file_name, object_file_info,
                               symbol_name, symbol_info)


def trim(memory_map: Dict[str, Any], args: Namespace) -> None:
    """Trim the memory map tree based on command line arguments. This removes
    unused memory types and sections and trims the dept of the tree if e.g.
    --archives is specified. It also removes all entries for the diff command if
    they were not changed."""
    def changed(diff: int) -> bool:
        if not args.diff or args.show_unchanged:
            return True
        return True if diff else False

    ARCHIVE_DETAILS, ARCHIVES, OBJECTS, ALL = range(4)

    if args.archive_details:
        depth = ARCHIVE_DETAILS
    elif args.archives:
        depth = ARCHIVES
    elif args.files:
        depth = OBJECTS
    else:
        depth = ALL

    if not args.show_unused:
        memory_map['memory_types'] = {k: v for k, v in memory_map['memory_types'].items()
                                      if v['used'] + abs(v['used_diff'])}

    memory_map['memory_types'] = {k: v for k, v in memory_map['memory_types'].items()
                                  if changed(v['used_diff'])}

    for mem_type_name, mem_type_info in memory_map['memory_types'].items():
        if not args.show_unused:
            # Remove sections, which do not have any archive. For example .iram0.text_end is defined
            # to mark the end of IRAM code segment and contains just an alignment.
            mem_type_info['sections'] = {k: v for k, v in mem_type_info['sections'].items()
                                         if v['archives']}
        mem_type_info['sections'] = {k: v for k, v in mem_type_info['sections'].items()
                                     if changed(v['size_diff'])}

        for section_name, section_info in mem_type_info['sections'].items():
            if depth == ARCHIVE_DETAILS:
                section_info['archives'] = {k: v for k, v in section_info['archives'].items()
                                            if v['abbrev_name'] == args.archive_details and
                                            changed(v['size_diff'])}
            else:
                section_info['archives'] = {k: v for k, v in section_info['archives'].items()
                                            if changed(v['size_diff'])}

            for archive_name, archive_info in section_info['archives'].items():
                if depth == ARCHIVES:
                    archive_info['object_files'] = {}
                    continue
                archive_info['object_files'] = {k: v for k, v in archive_info['object_files'].items()
                                                if changed(v['size_diff'])}

                for object_name, object_info in archive_info['object_files'].items():
                    if depth == OBJECTS:
                        object_info['symbols'] = {}
                        continue
                    object_info['symbols'] = {k: v for k, v in object_info['symbols'].items()
                                              if changed(v['size_diff'])}


def _get_summary_memory_types(memory_map: Dict[str, Any]) -> Dict[str, Any]:
    # Helper creating memory type/section dictionary for get_*_summary functions.
    mem_types: Dict[str, Any] = {}

    for mem_type_name, mem_type_info in memory_map['memory_types'].items():
        mem_types[mem_type_name] = {
            'size': 0,
            'size_diff': 0,
            'sections': {},
        }
        for section_name, section_info in mem_type_info['sections'].items():
            mem_types[mem_type_name]['sections'][section_name] = {
                'size': 0,
                'size_diff': 0,
                'abbrev_name': section_info['abbrev_name'],
            }

    return mem_types


def get_symbols_summary(memory_map: Dict[str, Any], args: Namespace) -> Dict[str, Any]:
    symbols: Dict[str, Any] = {}

    mem_types = _get_summary_memory_types(memory_map)
    found = False

    for (mem_type_name, mem_type_info,
         section_name, section_info,
         archive_name, archive_info,
         object_file_name, object_file_info,
         symbol_name, symbol_info) in walk(memory_map):

        if archive_info['abbrev_name'] != args.archive_details:
            continue

        found = True

        symbol_name_full = ':'.join([archive_name, object_file_name, symbol_name])
        if symbol_name_full not in symbols:
            symbol: Dict[str, Any] = {
                'abbrev_name': symbol_name,
                'size': 0,
                'size_diff': 0,
                'memory_types': copy.deepcopy(mem_types),
            }
            symbols[symbol_name_full] = symbol
        else:
            symbol = symbols[symbol_name_full]

        symbol_mem_type = symbol['memory_types'][mem_type_name]
        size = symbol_info['size']
        symbol_mem_type['sections'][section_name]['size'] = size
        symbol_mem_type['size'] += size
        symbol['size'] += size

        size = symbol_info['size_diff']
        symbol_mem_type['sections'][section_name]['size_diff'] = size
        symbol_mem_type['size_diff'] += size
        symbol['size_diff'] += size

    if not found:
        log.die(f'Archive "{args.archive_details}" not found.')

    symbols = {k: v for k, v in sorted(symbols.items(),
                                       key=lambda item: int(item[1]['size']),
                                       reverse=True)}

    return symbols


def get_object_files_summary(memory_map: Dict[str, Any], args: Namespace) -> Dict[str, Any]:
    object_files: Dict[str, Any] = {}

    mem_types = _get_summary_memory_types(memory_map)

    for (mem_type_name, mem_type_info,
         section_name, section_info,
         archive_name, archive_info,
         object_file_name, object_file_info,
         _, _) in walk(memory_map, depth='objects'):

        object_file_name_full = ':'.join([archive_name, object_file_name])
        if object_file_name_full not in object_files:
            object_file: Dict[str, Any] = {
                'abbrev_name': os.path.basename(object_file_name),
                'size': 0,
                'size_diff': 0,
                'memory_types': copy.deepcopy(mem_types),
            }
            object_files[object_file_name_full] = object_file
        else:
            object_file = object_files[object_file_name_full]

        object_file_mem_type = object_file['memory_types'][mem_type_name]
        size = object_file_info['size']
        object_file_mem_type['sections'][section_name]['size'] = size
        object_file_mem_type['size'] += size
        object_file['size'] += size

        size = object_file_info['size_diff']
        object_file_mem_type['sections'][section_name]['size_diff'] = size
        object_file_mem_type['size_diff'] += size
        object_file['size_diff'] += size

    object_files = {k: v for k, v in sorted(object_files.items(),
                                            key=lambda item: int(item[1]['size']),
                                            reverse=True)}

    return object_files


def get_archives_summary(memory_map: Dict[str, Any], args: Namespace) -> Dict[str, Any]:
    archives: Dict[str, Any] = {}

    mem_types = _get_summary_memory_types(memory_map)

    for (mem_type_name, mem_type_info,
         section_name, section_info,
         archive_name, archive_info,
         _, _,
         _, _) in walk(memory_map, depth='archives'):

        if archive_name not in archives:
            archive: Dict[str, Any] = {
                'abbrev_name': archive_info['abbrev_name'],
                'size': 0,
                'size_diff': 0,
                'memory_types': copy.deepcopy(mem_types),
            }
            archives[archive_name] = archive
        else:
            archive = archives[archive_name]

        archive_mem_type = archive['memory_types'][mem_type_name]
        size = archive_info['size']
        archive_mem_type['sections'][section_name]['size'] = size
        archive_mem_type['size'] += size
        archive['size'] += size

        size = archive_info['size_diff']
        archive_mem_type['sections'][section_name]['size_diff'] = size
        archive_mem_type['size_diff'] += size
        archive['size_diff'] += size

    archives = {k: v for k, v in sorted(archives.items(),
                                        key=lambda item: int(item[1]['size']),
                                        reverse=True)}

    return archives


def _filter_memory_regions(memory_regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    memory_regions_filtered: List[Dict[str, Any]] = []

    for mem_reg in memory_regions:
        if mem_reg['name'] == '*default*':
            # Skip default memory region
            continue
        memory_regions_filtered.append(mem_reg)

    log.debug(f'memory regions filtered', memory_regions_filtered)
    return memory_regions_filtered


def _split_memory_regions(memory_regions: List[Dict[str, Any]], memory_types: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Split memory regions according to memory types and assign each memory region a memory type.
    memory_regions_splitted: List[Dict[str, Any]] = []

    for mem_reg in memory_regions:
        mem_reg_length = mem_reg['length']
        mem_reg_origin = mem_reg['origin']

        while True:
            for mem_type_name, mem_type_info in memory_types.items():
                found = False
                mem_type_addr = mem_type_info['primary_address']
                mem_type_length = mem_type_info['length']
                if mem_type_addr <= mem_reg_origin < mem_type_addr + mem_type_length:
                    found = True
                elif mem_type_info['secondary_address']:
                    mem_type_addr = mem_type_info['secondary_address']
                    if mem_type_addr <= mem_reg_origin < mem_type_addr + mem_type_length:
                        found = True
                if not found:
                    continue

                used_length = min(mem_reg_length, mem_type_length - (mem_reg_origin - mem_type_addr))
                memory_regions_splitted.append({
                    'name': mem_reg['name'],
                    'origin': mem_reg_origin,
                    'length': used_length,
                    'attrs': mem_reg['attrs'],
                    'type': mem_type_info,
                })
                mem_reg_origin += used_length
                mem_reg_length -= used_length
                break
            else:
                # No memory type found for memory region. Check if it's a zero size
                # reserved region, which may have starting address at the end of
                # memory region for which the reservation is intended. For example
                # rtc_fast_reserved_seg for esp32. We could probably just skip
                # such memory regions, but let's sanity check this situation.
                for mem_reg_splitted in memory_regions_splitted.copy():
                    if mem_reg_origin + mem_reg_length == mem_reg_splitted['origin'] + mem_reg_splitted['length']:
                        memory_regions_splitted.append({
                            'name': mem_reg['name'],
                            'origin': mem_reg_origin,
                            'length': mem_reg_length,
                            'attrs': mem_reg['attrs'],
                            'type': mem_reg_splitted['type'],
                        })
                        break
                else:
                    # No memory type found, this region will be skipped.
                    log.warn(f'cannot assign memory region {mem_reg["name"]} to chip memory type')
                    break

            if not mem_reg_length:
                break

    log.debug(f'memory regions splitted', memory_regions_splitted)
    return memory_regions_splitted


def _filter_map_sections(sections: List[Dict[str, Any]], elf_sections: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sections_filtered: List[Dict[str, Any]] = []
    for section in sections:
        if not section['size']:
            # Remove empty sections.
            continue

        if section['name'].endswith(('dummy', 'reserved_for_iram')):
            # These are NOLOAD sections, which are used as a gap for overlapping memory
            # regions. For example on esp32s3 SRAM1 may be accessed via instruction and
            # data bus. iram0_0_seg memory range covers SRAM0+SRAM1, while dram0_0_seg covers SRAM1, so
            # iram0_0_seg may overlap into dram0_0_seg. The dummy section is used to "move"
            # the dram0_0_seg beginning according to the actual iram0_0_seg end. For more info
            # see linker scripts. These sections have SHF_ALLOC flag, because they occupy
            # memory during process execution, like bss, but the same space is actually loaded
            # with data from other section in the iram0_0_seg. Hence we would account the
            # space twice.
            continue

        if section['name'].endswith('noload'):
            # NOLOAD section used to dump data, which are not used during process
            # execution. It's placed as last section in memory region. For example
            # .flash.rodata_noload output section in drom0_0_seg(default_rodata_seg)
            # memory region.
            continue

        if elf_sections:
            if section['name'] not in elf_sections:
                # Section does not occupy memory during process execution, no SHF_ALLOC flag.
                continue
        else:
            # ELF sections are not available. Filter based on output section names.
            if (not section['name'].endswith(('.text', '.data', '.bss', '.rodata', 'noinit', '.vectors')) and
                    'flash' not in section['name'] and
                    'eh_frame' not in section['name']):
                continue

        # Remove input sections, which have zero size
        section['input_sections'] = [s for s in section['input_sections'] if s['size']]
        sections_filtered.append(section)

    log.debug(f'linker map output sections filtered', sections_filtered)
    return sections_filtered


def _split_map_sections(sections: List[Dict[str, Any]], regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sections_splitted: List[Dict[str, Any]] = []

    sections = sections.copy()

    while sections:
        section = sections.pop()
        for region in regions:
            if section['address'] < region['origin'] or section['address'] >= region['origin'] + region['length']:
                # Section is not part of this region
                continue
            if section['address'] + section['size'] <= region['origin'] + region['length']:
                # Sections fits into the region
                sections_splitted.append(section)
                break
            # Section spans across multiple memory types, so split it according to the memory type.
            split_addr = region['origin'] + region['length']
            split_size = split_addr - section['address']
            section1 = {
                'name': section['name'],
                'address': section['address'],
                'size': split_size,
                'input_sections': [],
            }
            section2 = {
                'name': section['name'],
                'address': split_addr,
                'size': section['size'] - split_size,
                'input_sections': [],
            }
            for input_section in section['input_sections']:
                input_section_end = input_section['address'] + input_section['size'] + input_section['fill']
                if input_section_end <= split_addr:
                    # Input section fully fits into new output section1
                    section1['input_sections'].append(input_section)
                elif input_section['address'] > split_addr:
                    # Input section fully fits into new output section2
                    section2['input_sections'].append(input_section)
                else:
                    # Input section overlaps split_addr, so we need to split it too
                    input_section1 = input_section.copy()
                    input_section1['symbols'] = []
                    input_section2 = input_section.copy()
                    input_section2['symbols'] = []

                    input_section1['size'] = min(split_addr - input_section['address'], input_section['size'])
                    input_section1['fill'] = split_addr - (input_section1['address'] + input_section1['size'])
                    input_section2['address'] = split_addr
                    input_section2['size'] = input_section['size'] - input_section1['size']
                    input_section2['fill'] = input_section['fill'] - input_section1['fill']

                    # Split symbols
                    for symbol in input_section['symbols']:
                        symbol_end_addr = symbol['address'] + symbol['size']
                        if symbol_end_addr <= split_addr:
                            # Symbol fully fits into new input section1
                            input_section1['symbols'].append(symbol)
                        elif symbol['address'] > split_addr:
                            # Symbol fully fits into new input section2
                            input_section2['symbols'].append(symbol)
                        else:
                            # Symbol overlaps split_addr, so we need to split it too
                            symbol1 = symbol.copy()
                            symbol2 = symbol.copy()

                            symbol1['size'] = split_addr - symbol['address']
                            symbol2['address'] = split_addr
                            symbol2['size'] = symbol['size'] - symbol1['size']

                            input_section1['symbols'].append(symbol1)
                            input_section2['symbols'].append(symbol2)

                    section1['input_sections'].append(input_section1)
                    section2['input_sections'].append(input_section2)
                    log.debug(f'linker map input section {input_section["name"]} splitted at address {split_addr}',
                              input_section, input_section1, input_section2)

            sections_splitted.append(section1)
            sections.append(section2)
            log.debug(f'linker map output section {section["name"]} splitted at address {split_addr}',
                      section, section1, section2)
            break
        else:
            # Output section or its part does not fit into any memory region. Just add it as it is.
            sections_splitted.append(section)

    log.debug(f'linker map output sections splitted', sections_splitted)
    return sections_splitted


def _abbrev(section_name: str) -> str:
    splitted = section_name.split('.')
    return f'.{splitted[-1]}'


def _get_project_description_fn(fn: str) -> str:
    dirname = os.path.dirname(fn)
    fn = os.path.join(dirname, 'project_description.json')
    return fn


def _get_project_description(fn: str) -> Optional[Dict[str, Any]]:
    proj_desc = None
    try:
        with open(fn, 'r') as f:
            proj_desc = json.load(f)
    except (OSError, ValueError) as e:
        log.debug(f'project_description.json is not available: {e}')

    log.debug('project_description.json', proj_desc)
    return proj_desc


def _load_elf_file(fn: str) -> Optional[ELFFile]:
    try:
        elf = ELFFile.load_from_path(fn)
    except (OSError, ValueError) as e:
        log.die(f'cannot read project ELF file: {e}')
    except ELFError as e:
        log.die(f'cannot parse ELF file sections: {e}')

    log.debug(f'elf file {fn}')
    return elf


def _add_symbols_to_sections(elf: Optional[ELFFile], osections: List[Dict[str, Any]]) -> None:
    if not elf:
        # ELF is not available. Use input section names as symbols.
        for osec in osections:
            for isec in osec['input_sections']:
                isec['symbols'] = [{
                    'name': isec['name'],
                    'address': isec['address'],
                    'size': isec['size'],
                }]
        return

    # Get dictionary of symbols from ELF for STT_FUNC and STT_OBJECT and sort it based
    # on symbol address.
    symbols: List[Symbol] = []
    for section in elf.iter_sections():
        if section.header['sh_type'] != 'SHT_SYMTAB':
            continue
        symtab = elf.get_section_by_name(section.name)
        for symbol in symtab.iter_symbols():
            if symbol['st_info']['type'] not in ['STT_FUNC', 'STT_OBJECT'] or not symbol['st_size']:
                # Skip uninteresting symbols
                continue
            symbols.append(symbol)

    symbols = [s for s in sorted(symbols, key=lambda s: s['st_value'] or 0)]  # or 0 help mypy

    # Get list of input sections, sorted by address, and add symbols list to each
    # input section.
    isections: List[Dict[str, Any]] = []
    for osec in osections:
        for isec in osec['input_sections']:
            isec['symbols'] = []
            isections.append(isec)

    isections = [s for s in sorted(isections, key=lambda s: s.get('address', 0))]  # s.get used to help mypy

    # Add ELF symbols into input sections
    isec = isections.pop(0)
    for symbol in symbols:
        sym_name = symbol.name
        sym_addr = symbol['st_value']
        sym_size = symbol['st_size']
        while sym_addr >= isec['address'] + isec['size']:
            if not isections:
                # Sanity check that we found input section for symbol
                log.die(f'cannot find input section for symbol {sym_name}({sym_addr})')

            if not isec['symbols']:
                # Input section does not have any ELF symbols assigned.
                # In e.g. .data or .rodata sections, there might be literals, which do not have symbols
                # in symbol table. Since the binary is compiled with -fdata-sections, let's add the input
                # section as "symbol". This should avoid displaying "holes" in the reports. Generally it's
                # still possible that some libraries/objects, which are e.g. not compiled with -fdata-sections,
                # may still be missing some "symbols". For example libc.a->lib_a-vfprintf.o: 657 != 117
                # lib_a-vfprintf.o 657
                # ├── blanks.1 16
                # ├── zeroes.0 16
                # ├── .rodata.str1.4 53
                # └── .srodata.cst8 32
                isec['symbols'].append({
                    'name': isec['name'],
                    'address': isec['address'],
                    'size': isec['size'],
                })

            # Jump to next input section
            isec = isections.pop(0)

        if sym_addr + sym_size > isec['address'] + isec['size']:
            # Sanity check that symbol fits into input section
            log.die((f'symbol name: {sym_name}, addr: {sym_addr}, size: {sym_size} '
                     f'does not fit into input section name: {isec["name"]}, '
                     f'addr: {isec["address"]}, size: {isec["size"]}'))

        if sym_addr < isec['address']:
            # Symbol is not part of the current input section. It must be
            # ROM mappend symbol.
            continue

        # Append '()' to function symbol
        if symbol['st_info']['type'] == 'STT_FUNC':
            sym_name += '()'

        isec['symbols'].append({
            'name': sym_name,
            'address': sym_addr,
            'size': sym_size,
        })

    log.debug(f'linker map output sections filtered with symbols', osections)


def _get_elf_sections_headers(elf: Optional[ELFFile]) -> Optional[Dict[str, Any]]:
    if not elf:
        return None

    hdrs: Dict[str, Any] = {}
    sections_headers = {s.name: dict(s.header) for s in elf.iter_sections()}

    for name, info in sections_headers.items():
        if info['sh_size'] == 0:
            # Section has zero memory size, so skip it
            continue
        if not info['sh_flags'] & SH_FLAGS.SHF_ALLOC:
            # Section doesn't occupy memory during app execution, so skip it
            continue
        hdrs[name] = info

    log.debug('elf section headers', hdrs)

    return hdrs


def _get_image_size(elf_sections: Optional[Dict[str, Any]], sections: List[Dict[str, Any]]) -> int:
    size = 0
    if not elf_sections:
        # ELF information not available
        for sec in sections:
            if sec['name'].endswith('.bss'):
                continue
            size += sec['size']
        return size

    for name, info in elf_sections.items():
        if info['sh_type'] != 'SHT_PROGBITS':
            continue
        size += info['sh_size']

    return size


def _add_archives_to_sections(sections: List[Dict[str, Any]]) -> None:
    for section in sections:
        archives: Dict[str, Any] = {}
        for input_section in section['input_sections']:
            archive_name = input_section['archive']
            if archive_name not in archives:
                archive = {
                    'abbrev_name': os.path.basename(archive_name),
                    'size': 0,
                    'size_diff': 0,
                    'object_files': {},
                }
                archives[archive_name] = archive
            else:
                archive = archives[archive_name]

            archive['size'] += input_section['size']

            object_file_name = input_section['object_file']
            if object_file_name not in archive['object_files']:
                object_file = {
                    'abbrev_name': os.path.basename(object_file_name),
                    'size': 0,
                    'size_diff': 0,
                    'symbols': {},
                }
                archive['object_files'][object_file_name] = object_file
            else:
                object_file = archive['object_files'][object_file_name]

            object_file['size'] += input_section['size']

            for symbol in input_section['symbols']:
                object_file['symbols'][symbol['name']] = {
                    'abbrev_name': symbol['name'],
                    'size': symbol['size'],
                    'size_diff': 0,
                }

        section['abbrev_name'] = _abbrev(section['name'])
        section['archives'] = archives

    log.debug('sections with archives', sections)


def _get_memory_types(target: str) -> Dict[str, Any]:
    # Load memory types from yml file
    memory_types: Dict[str, Any] = {}
    try:
        directory = os.path.dirname(__file__)
        fn = os.path.join(directory, '..', 'chip_info', target + '.yaml')
        with open(fn, 'r') as f:
            memory_types = yaml.safe_load(f)
    except (OSError, ValueError) as e:
        log.die(f'cannot read memory types file: {e}')

    for name, info in memory_types.items():
        info['primary_address'] = eval(str(info['primary_address']))
        info['length'] = eval(str(info['length']))
        if 'secondary_address' in info:
            info['secondary_address'] = eval(str(info['secondary_address']))
        else:
            info['secondary_address'] = 0

        if 'name' not in info:
            info['name'] = name

    log.debug(f'memory types for {target}', memory_types)

    return memory_types


def _get_mem_type_map(memory_types: Dict[str, Any],
                      memory_regions: List[Dict[str, Any]],
                      map_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    memory_map: Dict[str, Any] = {}
    # Dictionary of memory types, where key is memory type alias and value is a list of memory regions, which
    # were already assigned to this memory type.
    memory_types_regions: Dict[str, Any] = {}

    # Create entry for each memory type found in the chip info yaml.
    for mem_type_name, mem_type_info in memory_types.items():
        mem_type_alias = mem_type_info['name']
        memory_map[mem_type_alias] = {
            'size': 0,
            'size_diff': 0,
            'used': 0,
            'used_diff': 0,
            'sections': {},
        }
        memory_types_regions[mem_type_alias] = []

    # Calculate memory type sizes based on the memory regions found in linker map file
    for mem_reg in memory_regions:
        mem_type_info = mem_reg['type']
        mem_type_alias = mem_type_info['name']
        if not memory_types_regions[mem_type_alias]:
            # This memory type does not yet have any memory region assigned
            memory_map[mem_type_alias]['size'] = mem_reg['length']
            memory_types_regions[mem_type_alias].append(mem_reg)
        else:
            # There are some memory regions assigned to this memory type. We need to check
            # if the memory region, which is currently being added, isn't an alias for already
            # added memory region. This is for example case of DIRAM.
            mem_type_offset = 0
            if mem_type_info['secondary_address']:
                mem_type_offset = abs(mem_type_info['primary_address'] - mem_type_info['secondary_address'])
            for mem_type_reg in memory_types_regions[mem_type_alias]:
                mem_reg_offset = abs(mem_type_reg['origin'] - mem_reg['origin'])
                if mem_type_offset == mem_reg_offset and mem_type_reg['length'] == mem_reg['length']:
                    # The current memory region has the same offset to the already added memory region as
                    # offset in memory type(primary and secondary address offset). The length also matches, so this
                    # memory region is mapped into the same memory as region that was already added to the
                    # memory type. Skip it, so we don't account the size of the memory region twice into the total
                    # memory type size.
                    memory_types_regions[mem_type_alias].append(mem_reg)
                    log.debug(f'found memory region alias', mem_reg, mem_type_reg)
                    break
            else:
                # Another memory region, which needs to be added to the memory type. We have not found
                # any alias for this one and it does not overlap with already added memory regions, so
                # account its size into the total memory type size.
                memory_map[mem_type_alias]['size'] += mem_reg['length']
                memory_types_regions[mem_type_alias].append(mem_reg)

    # Add linker output sections into memory types.
    memory_regions_sorted = [r for r in sorted(memory_regions, key=lambda r: r['origin'] or 0)]
    for map_section in map_sections:
        prev_mem_reg = None
        for mem_reg in memory_regions_sorted:
            address = mem_reg['origin']
            mem_type_alias = mem_reg['type']['name']
            if address <= map_section['address'] < address + mem_reg['length']:
                if map_section['address'] + map_section['size'] > address + mem_reg['length']:
                    # Sanity check that output sections fits into memory region. This should probably never happen.
                    log.warn((f'output section {map_section["name"]}(addr: {map_section["address"]}, '
                              f'size: {map_section["size"]}) exceeds memory region "{mem_reg["name"]}" '
                              f'(addr: {address}, size: {mem_reg["length"]})'))

                memory_map[mem_type_alias]['used'] += map_section['size']
                memory_map[mem_type_alias]['sections'][map_section['name']] = {
                    'abbrev_name': map_section['abbrev_name'],
                    'size': map_section['size'],
                    'size_diff': 0,
                    'archives': map_section['archives'],
                }
                break
            elif address > map_section['address'] and prev_mem_reg:
                mem_type_alias = prev_mem_reg['type']['name']

                # Output section does not map into any memory region. This may happen e.g. when memory region
                # is not big enough and the linker fails. In this case try to map the output section into the
                # first memory region/type preceding the output section.
                log.warn((f'[red]{mem_type_alias} overflow detected![/red]: '
                          f'output section or its part {map_section["name"]}(addr: {map_section["address"]}, '
                          f'size: {map_section["size"]}) does not fit into any memory region and '
                          f'will be assigned to the preceding {prev_mem_reg["name"]} memory region'))

                # During overflow the output section could be split according to memory region, which
                # is smaller than the output section. Meaning there will be to output section with the
                # same name. One which was split and fully fits into the memory region and second which
                # represents the overflow part. Since we could be mapping the overflow part into the same
                # region, which may already contain the first part, we would overwrite it, because the
                # output section names are used as key in the memory map dictionary. To overcome this and
                # clearly mark the overflow part of the output memory section, append "_overflow" to its name.
                map_section_name = map_section['name'] + '_overflow'

                memory_map[mem_type_alias]['used'] += map_section['size']
                memory_map[mem_type_alias]['sections'][map_section_name] = {
                    'abbrev_name': _abbrev(map_section_name),
                    'size': map_section['size'],
                    'size_diff': 0,
                    'archives': map_section['archives'],
                }
                break

            prev_mem_reg = mem_reg

        else:
            log.warn((f'cannot assign output section {map_section["name"]}(addr: {map_section["address"]}, '
                      f'size: {map_section["size"]}) to any memory type'))

    return memory_map
