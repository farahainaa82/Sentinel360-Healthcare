# Troubleshooting Guide

## Issue: "2D-7 manifest not found"
**Cause**: The 2D-7 manifest file is missing or misnamed.
**Solution**: Re-run 2D-7 or ensure `step_2d7_manifest.json` exists in `outputs/decision_intelligence/`.

## Issue: "Checksum mismatch"
**Cause**: A 2D-7 output file was modified after manifest generation.
**Solution**: Do not modify 2D-7 outputs. Re-run 2D-7 if regeneration is needed.

## Issue: "Brief register empty"
**Cause**: `step_2d7_integrated_management_brief_register.csv` is missing or empty.
**Solution**: Verify 2D-7 completed successfully and produced the register.

## Issue: Engine raises KeyError
**Cause**: A 2D-7 register is missing expected columns.
**Solution**: Check the upstream register structure. The engine logs the missing column.

## Issue: "Expected 646 packages, found X"
**Cause**: 2D-7 did not produce the expected number of packages.
**Solution**: Investigate upstream phases 2D-1 through 2D-7.

## Issue: Tests fail with ModuleNotFoundError
**Cause**: PYTHONPATH does not include `src/`.
**Solution**: Run tests from the project root with `python -m pytest tests/...`.

## Issue: Population count mismatch
**Cause**: Some registers have different row counts than expected.
**Solution**: Check if the register is 1:1 (646), 1:17 (10982), or 1:8 (5168) and adjust expectations.

## Issue: Prohibited terms found
**Cause**: Governance wording violations exist in 2D-7 data.
**Solution**: This is a real finding. Apply governance correction or adjust the prohibited terms config.

## Issue: Scenario summaries missing
**Cause**: Some packages lack scenario data.
**Solution**: Verify 2D-5 scenario generation completed for all applicable packages.
