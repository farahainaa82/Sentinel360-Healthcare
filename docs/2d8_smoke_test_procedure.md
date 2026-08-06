# Smoke Test Procedure

## Purpose
Verify the 2D-8 validation pipeline runs end-to-end on a representative sample before executing the full 646-package run.

## Sample Selection
The smoke test automatically selects 5 packages covering different readiness statuses:
1. Ready for Integrated Management Review
2. Ready with Conditions
3. Monitoring Only
4. Requires Assumption Validation
5. Non-Quantitative

If any status is missing, the sample is filled from the first available rows.

## Execution
```bash
cd src
python run_decision_intelligence_validation_2d8.py --smoke
```

## Expected Results
- All 26 engines execute without ERROR status
- Pipeline completes in under 5 seconds
- 32 output files are generated
- Manifest contains `mode: smoke_test`

## Decision Gate
- **PASS**: All engines complete, no uncaught exceptions
- **FAIL**: Any engine raises an exception or manifest is not written
- **Action if FAIL**: Debug the failing engine before full run

## Notes
- Smoke test engines read the full 2D-7 registers (not a subset)
- Per-package summary is limited to the 5 sample packages
- Some validation checks may show FAIL due to real data findings; this is expected
