# Full Run Procedure

## Prerequisites
1. All 2D-7 outputs present in `outputs/decision_intelligence/`
2. 2D-7 manifest valid and checksums verified
3. Smoke test passed
4. All 11 config files present in `config/`

## Execution
```bash
cd src
python run_decision_intelligence_validation_2d8.py --full
```

## What Happens
1. **Authority check**: SHA-256 checksums verified for all 2D-7 outputs
2. **Population check**: Row counts reconciled across all registers
3. **Identity check**: 646 unique IDs confirmed
4. **25 additional dimensions**: Each engine runs validation checks
5. **Per-package summary**: 646 rows with outcomes and correction classes
6. **Output generation**: 32 registers written atomically
7. **Manifest generation**: JSON manifest with full metadata

## Timing
- Typical execution time: 2-3 seconds
- Memory footprint: Low (streaming DataFrame operations)

## Output Verification
After completion, verify:
```bash
python -m pytest tests/test_step_2d8_decision_intelligence_validation.py -v
```

All 108 tests should pass.

## Post-Run Checklist
- [ ] 646 packages validated
- [ ] 32 output files present
- [ ] Manifest valid JSON
- [ ] All tests pass
- [ ] No 2D-9 artifacts created
