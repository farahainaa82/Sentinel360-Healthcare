# 2D-8 Architecture and Design

## Component Diagram

```
+-----------------------------------------------------------+
|  Frozen 2D-7 Outputs (29 CSV + 1 manifest)                |
+-----------------------------------------------------------+
                            |
                            v
+-----------------------------------------------------------+
|  decision_intelligence_validation_utils.py                |
|  - load_register()   - atomic_write_csv()                 |
|  - compute_sha256()  - validation_outcome()               |
|  - correction_class()                                     |
+-----------------------------------------------------------+
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
   [26 Validation Engines] [11 Config Files]  [Main Runner]
        |                   |                   |
        +-------------------+-------------------+
                            |
                            v
+-----------------------------------------------------------+
|  2D-8 Outputs (32 registers A-AF)                         |
|  - step_2d8_master_validation_register.csv                |
|  - step_2d8_manifest.json                                 |
+-----------------------------------------------------------+
```

## Engine Classification

### Critical (must pass for Streamlit handover)
- authority, identity, action_routing, governance

### High (focused correction required if failed)
- kpi_risk, financial, readiness, evidence, lineage, wording

### Medium (conditions documented if failed)
- scenario, narrative, contradiction, cross_layer, streamlit

### Low (informational)
- question, confirmation, monitoring, recommendation, tradeoff, export_contract, priority_queue, section, type, audit, population

## Execution Flow
1. Load frozen 2D-7 manifest and verify checksums
2. Execute 26 validation engines sequentially
3. Build per-package validation summary (646 rows)
4. Determine validation outcome and correction classification per package
5. Write all 32 output registers atomically
6. Build and write manifest
