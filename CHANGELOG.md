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
