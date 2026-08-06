# Test Coverage Report

## Test Suite: test_step_2d8_decision_intelligence_validation.py

### Summary
- **Total tests**: 108 (69 distinct test functions + parametrized variants)
- **Pass rate**: 100%
- **Execution time**: ~1 second

### Coverage Areas

#### Config Files (T001-T015)
- 11 config files exist and are non-empty
- Rule config has required columns
- Outcome scale has 7 levels
- Correction classification has 8 classes
- Streamlit readiness has 17 components

#### Output Files (T016-T045)
- All 32 output registers (A-AF) exist
- Manifest is valid JSON
- Master register has 646 rows
- Execution summary lists 26 engines
- Outcome distribution sums to 646

#### Engine-Specific (T054-T084)
- Authority: all files exist, checksums match
- Population: all counts match
- Identity: IDs unique, no nulls
- KPI/Risk: escalation alignment
- Action Routing: no pre-selection, all pending
- Narrative: word counts within limits
- Wording: no prohibited terms, no causal language
- Governance: boundary present, term count zero
- Export: row count correct
- Section: 17 per package
- Streamlit: contract populated
- Evidence/Lineage: upstream reconciliation
- Audit: status awaiting
- Financial: confidence range
- Readiness: upstream match
- Cross-Layer: score range, governance issues
- Recommendation: confidence range, no pre-approval
- Questions: blocking count non-negative
- Confirmations: pending count present
- Monitoring: escalation valid
- Tradeoff: displacement risk present
- Priority Queue: row counts
- Type: register count

#### Edge Cases (T085-T094)
- No duplicate package IDs
- Non-negative failure counts
- Boolean streamlit_ready
- No null outcome categories
- Positive elapsed times
- Manifest outputs match files

#### Runner Integrity (T095-T104)
- Runner imports successfully
- Utils functions exposed
- All engines have build_register
- Correction class mapping complete
- Validation outcome severity mapping correct
- Outcome values governed
- Correction values governed
- No pre-approved recommendations
- Causality not confirmed
- Governance issue count zero

#### Final Integrity (T105-T108)
- All CSV outputs have checksums
- Manifest timestamp present
- Passes + fails = checks
- Stop before 2D-9 marker
