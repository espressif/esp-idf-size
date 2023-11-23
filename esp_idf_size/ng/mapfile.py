# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import re
from typing import Any, Dict, List, Tuple

from . import log


class MapFile:
    def __init__(self, fn:str) -> None:
        self.fn = fn
        self.lines = self._get_mapfile_lines(fn)
        self.line_idx = 0
        self.memory_regions = self._get_memory_regions()
        self.target = self._get_target()
        self.sections = self._get_sections()
        self._validate_sections(self.sections)

    def _get_mapfile_lines(self, fn: str) -> List[str]:
        try:
            with open(fn, 'r') as f:
                lines = f.read().splitlines()
        except (OSError, ValueError) as e:
            log.die(f'cannot read linker map file: {e}')

        return lines

    def _get_memory_regions(self) -> List[Dict[str, Any]]:
        regions: List[Dict[str, Any]] = []
        found = False
        header = False
        for ln, line in enumerate(self.lines[self.line_idx:]):
            if line.startswith('Linker script and memory map'):
                break

            if not found:
                if line.startswith('Memory Configuration'):
                    found = True
                continue

            if not header:
                if line.startswith('Name'):
                    header = True
                continue

            splitted = line.split()
            if not splitted:
                # Empty line after memory regions
                continue
            if len(splitted) == 4:
                name, origin, length, attrs = splitted
            elif len(splitted) == 3:
                name, origin, length = splitted
                attrs = ''
            else:
                log.die((f'unexpected format of memory region "{line}" at line {ln+1} in '
                         f'"Memory Configuration" section in "{self.fn}" map file'))

            regions.append({
                'name': name,
                'origin': int(origin, 0),
                'length': int(length, 0),
                'attrs': attrs
            })

        if not found or not header:
            log.die(f'cannot parse "Memory Configuration" section in "{self.fn}" map file')

        log.debug('linker map memory regions', regions)

        # Skip already processed lines
        self.line_idx += ln

        return regions

    def _get_target(self) -> str:
        # Original esp-idf-size regexes
        RE_TARGET = re.compile(r'IDF_TARGET_(\S*) =')
        # For back-compatible with cmake in idf version before 5.0
        RE_TARGET_CMAKEv4x = re.compile(r'project_elf_src_(\S*)\.c.obj')
        # For back-compatible with make
        RE_TARGET_MAKE = re.compile(r'^LOAD .*?/xtensa-(esp[^-]+)-elf/')

        target = ''
        found = False
        for ln, line in enumerate(self.lines[self.line_idx:]):
            if line.startswith('Cross Reference Table'):
                # We have reached end of the "Linker script and memory map" section.
                log.warn(f'cannot find target in linker map file')
                break

            elif not found:
                # Continue here till we find the beginning of linker scripts section.
                if line.startswith('Linker script and memory map'):
                    found = True
                    continue

            match_target = RE_TARGET.search(line)
            if match_target:
                target = match_target.group(1).lower()
                break

            match_target = RE_TARGET_CMAKEv4x.search(line)
            if match_target:
                target = match_target.group(1)
                break

            match_target = RE_TARGET_MAKE.search(line)
            if match_target:
                target = match_target.group(1)
                break

        # Don't skip the lines, because the same lines will be scanned by follow-up _get_sections
        # self.line_idx += ln
        return target

    def _get_sections(self) -> List[Dict[str, Any]]:
        def get_archive_object_file(s: str) -> Tuple[str,str]:
            idx = s.find('(')
            if idx == -1:
                # Object file linked directly without archive. As in the original parser,
                # assign a default archive for such object file.
                return ('(exe)', s)
            archive = s[:idx]
            object_file = s[idx + 1:-1]
            return (archive, object_file)

        def add_input_section(output_section: Dict[str, Any], input_section: Dict[str, Any]) -> None:
            '''
            The linker map may contain input sections with different sizes at the same address. This
            seems to be related to the -Og and separated function/data sections. The logic behind this
            still eludes me and it would be nice to fully understand what's going on in these situations and
            why the linker adds such sections. Maybe it's just related to the -Og.

            Makefile
            --------
            OBJS = test.o test2.o
            PROJ=test

            all: $(PROJ)

            %.o: %.c
                    gcc -ffunction-sections -fdata-sections -Og -c -o $@ $<
            $(PROJ): $(OBJS)
                    gcc -Wl,-Map,$@.map -o $@ $?

            clean:
                    rm -rf $(OBJS) $(PROJ) $(PROJ).map

            test.c
            --------
            #include <stdio.h>

            char* msg = "how are you";
            extern char *msg2;

            void test(const char *c)
            {
                    printf("%s", c);
            }

            int main(int argc, char *argv[])
            {
                    printf("%s\n", msg);
                    test(msg2);
            }
            test2.c
            --------
            char* msg2 = "hello how are you";

            test.map
            --------
             .rodata.str1.1
                            0x0000000000402013        0x3 test.o
                                                      0xc (size before relaxing)
             .rodata.str1.1
                            0x0000000000402013       0x12 test2.o
            '''
            if not output_section['input_sections']:
                output_section['input_sections'].append(input_section)
                return
            last_input_section = output_section['input_sections'][-1]
            if last_input_section['address'] == input_section['address']:
                # The current input section is at the same address as the previous one,
                # so set the previous input section size to 0, because it's not part
                # of the final image.
                last_input_section['size'] = 0

            if not input_section['size'] and input_section['fill']:
                # Input section has the same address as *fill*, so account the *fill*
                # size to the latest input section with non zero size. Note that
                # parser sets size to zero for such sections, but keeps the fill size,
                # so it can be accounted here.
                for s in reversed(output_section['input_sections']):
                    if s['size']:
                        s['fill'] += size
                        break
                input_section['fill'] = 0
            output_section['input_sections'].append(input_section)

        output_sections: List[Dict[str, Any]] = []
        output_section: Dict[str, Any] = {}
        input_section: Dict[str, Any] = {}
        in_output_section = False
        in_input_section = False
        found = False
        for ln, line in enumerate(self.lines[self.line_idx:]):
            if line.startswith('Cross Reference Table'):
                # We have reached end of the "Linker script and memory map" section.
                break

            elif not found:
                # Continue here till we find the beginning of linker scripts section.
                if line.startswith('Linker script and memory map'):
                    found = True

            elif in_output_section:
                # We are in output section
                line = line.strip()
                if not line:
                    # Empty line marks end of output section
                    if input_section:
                        add_input_section(output_section, input_section)
                    output_sections.append(output_section)
                    in_output_section = False
                    in_input_section = False
                    output_section = {}
                    input_section = {}

                elif output_section['address'] is None:
                    # Missing address and length key means that the output section info
                    # is splitted on two lines. Fill in the missing address and length here.
                    splitted = line.split()
                    if len(splitted) != 2:
                        log.die((f'unexpected output section continuous line "{line}" at line {ln+1} in '
                                 f'"Linker script and memory map" section in "{self.fn}" map file'))
                    output_section['address'] = int(splitted[0], 0)
                    output_section['size'] = int(splitted[1], 0)

                elif line.startswith('.'):
                    # New input section
                    if input_section:
                        add_input_section(output_section, input_section)
                    input_section = {
                        'name': None,
                        'address': None,
                        'size': None,
                        'archive': '',
                        'object_file': '',
                        'fill': 0,
                    }
                    splitted = line.split()
                    if len(splitted) == 1:
                        # Same as for output section. We have just the name and the rest is on the next line.
                        in_input_section = True
                        input_section['name'] = splitted[0]
                    elif len(splitted) == 4:
                        input_section['name'] = splitted[0]
                        input_section['address'] = int(splitted[1], 0)
                        input_section['size'] = int(splitted[2], 0)
                        input_section['archive'], input_section['object_file'] = get_archive_object_file(splitted[3])
                    else:
                        log.die((f'unexpected format of input section "{line}" at line {ln+1} in '
                                 f'"Linker script and memory map" section in "{self.fn}" map file'))

                elif in_input_section:
                    if input_section['address'] is None:
                        # Handle input section address, size and archive(object_file) on a separate line
                        splitted = line.split()
                        if len(splitted) != 3:
                            log.die((f'unexpected input section continuous line "{line}" at line {ln+1} in '
                                     f'"Linker script and memory map" section in "{self.fn}" map file'))
                        input_section['address'] = int(splitted[0], 0)
                        input_section['size'] = int(splitted[1], 0)
                        input_section['archive'], input_section['object_file'] = get_archive_object_file(splitted[2])

                    elif line.startswith('*fill*'):
                        splitted = line.split()
                        if len(splitted) != 3:
                            log.die((f'unexpected "*fill*" line "{line}" at line {ln+1} in '
                                     f'"Linker script and memory map" section in "{self.fn}" map file'))
                        address = int(splitted[1], 0)
                        size = int(splitted[2], 0)
                        if input_section['address'] == address:
                            # Input section address is the same as *fill* address. Set input
                            # section size to zero, but keep the *fill* size. It will be accounted
                            # in add_input_section.
                            input_section['size'] = 0

                        input_section['fill'] += size

            elif line.startswith('.'):
                # Detected new output section. There are two cases
                # 1. Section name, address and length on a single line
                #
                #    .rtc.text       0x0000000040070000        0x0
                #
                # 2. Section name on a single line, followed by address and length on a new line.
                #    LD is splitting output section info on two lines if the output section name
                #    exceeds 16 characters.
                #
                #    .rtc.force_slow
                #                    0x0000000050000000        0x0
                #
                # Output section start at the beginning of line and ends with empty line. All lines,
                # representing the input sections, within it are indented.
                in_output_section = True
                output_section = {
                    'name': None,
                    'address': None,
                    'size': None,
                    'input_sections': [],
                }

                splitted = line.split()
                if len(splitted) == 1:
                    output_section['name'] = splitted[0]
                elif len(splitted) == 3:
                    output_section['name'] = splitted[0]
                    output_section['address'] = int(splitted[1], 0)
                    output_section['size'] = int(splitted[2], 0)
                else:
                    log.die((f'unexpected format of output section "{line}" at line {ln+1} in '
                             f'"Linker script and memory map" section in "{self.fn}" map file'))

        if not found:
            log.die('cannot parse "Linker script and memory map" section in "{self.fn}" map file')

        log.debug('linker map output sections', output_sections)

        # Skip already processed lines
        self.line_idx += ln

        return output_sections

    def _validate_sections(self, sections: List[Dict[str, Any]]) -> None:
        for section in sections:
            start_addr = section['address']
            offset = 0
            for input_section in section['input_sections']:
                if not input_section['size']:
                    continue
                if start_addr + offset != input_section['address']:
                    log.die(f'input section {input_section["name"]} is not at expected address {hex(start_addr+offset)}')
                offset += input_section['size'] + input_section['fill']
