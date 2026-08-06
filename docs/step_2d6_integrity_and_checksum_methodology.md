# Integrity and Checksum Methodology

## Overview

Phase 2D-6 verifies the integrity of all authoritative inputs using SHA-256 checksums. Any integrity failure halts processing to prevent corrupted or tampered data from entering the audit layer.

## Checksum Algorithm

- **Algorithm**: SHA-256 (Secure Hash Algorithm 2, 256-bit)
- **Encoding**: Hexadecimal string, lowercase
- **Input**: File contents read in binary mode
- **Output**: 64-character hex digest

## Integrity Check Process

1. **Load authoritative input register**: Reads `step_2d6_authoritative_input_register.csv` (21 files).
2. **Compute checksums**: SHA-256 computed for each file at runtime.
3. **Compare with frozen checksums**: Where a frozen checksum exists from 2D-5, it is compared.
4. **Flag mismatches**: Any mismatch sets `checksum_match` = False and `integrity_failure_flag` = True.
5. **Halt on failure**: If any integrity failure is detected, processing stops before any 2D-6 outputs are written.

## Integrity Register Fields

| Field | Description |
|---|---|
| `file_name` | Name of the file checked |
| `checksum_algorithm` | Always "SHA-256" |
| `computed_checksum` | Runtime-computed SHA-256 digest |
| `frozen_checksum` | Checksum recorded at freeze time (if any) |
| `checksum_match` | True if computed == frozen |
| `integrity_failure_flag` | True if mismatch detected |
| `immutable_flag` | True if file is marked frozen |

## Governance Rules

- Integrity failures stop processing: no 2D-6 outputs are generated if any checksum fails.
- Frozen files are immutable: their checksums must match exactly.
- Superseded files are checked but do not halt processing if mismatched (they are not active).
- All checksums are logged in the integrity register for audit.

## Verified Results

- 21 authoritative input files checked.
- 21 checksums verified.
- 0 integrity failures.
- All frozen upstream files unchanged.

## Output

- `step_2d6_integrity_register.csv` (21 rows)
