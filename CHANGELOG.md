## v1.6.1 (2024-11-08)

### Bug Fixes

- add support for external RAM memory type for esp32p4
- cross reference table with empty symbol name
- input section address not within output section range

### Code Refactoring

- **ci**: update esp-idf-size legacy tests to pytest

## v1.6.0 (2024-09-10)

### New Features

- add archives' dependencies report

### Bug Fixes

- update the memory type ranges for the esp32c5
- handle archive paths that contain spaces

## v1.5.0 (2024-06-17)

### New Features

- **ng**: add filtering for archives, files, and symbols in table and CSV formats
- **ng**: initial support for memorymap API

### Bug Fixes

- correctly handle DIRAM and overflows reports

## v1.4.0 (2024-05-20)

### New Features

- **ng**: support for projects built with enabled LTO
- **ng**: initial version of ELF/DWARF parser
- add --unify option allowing to aggregate size information

### Bug Fixes

- **ng**: handle output sections with no content in map file
- **ng**: fix line enumeration in link map file parser
- **ng**: remove console width limit
- **ng**: fix map and elf file detection
- **ng**: fix memory map trimming for diff output

## v1.3.0 (2024-04-15)

### New Features

- **ng**: add support for output format sorting
- **esp32c61**: basic size support

### Bug Fixes

- **ng**: input section address not within output section range
- do not account noinit sections into total image size
- account only output sections with ".flash" string into flash memory
- account SRAM1 into IRAM size on esp32

## v1.2.0 (2024-03-18)

### New Features

- **ng**: add explicit bytes support

## v1.1.1 (2024-02-07)

### Bug Fixes

- **ng**: correctly set input section stage in linker map parser
- **ng**: provide more verbose error message when parsed map file validation fails

## v1.1.0 (2024-01-31)

### New Features

- **esp32c5**: base support of esp32c5

## v1.0.3 (2024-01-05)

### Bug Fixes

- **ng**: handle alignment/fill in section validation
