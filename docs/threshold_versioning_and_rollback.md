# Sentinel360 — Threshold Versioning and Rollback

## Step 2B-1B

---

## 1. Version Lifecycle

| Version | Stage | Description |
|---------|-------|-------------|
| v1.0-draft | Initial | Draft thresholds from early configuration |
| v1.0-candidate | Calibration | Provisional candidates from Step 2B-1A |
| v1.0-approved | Promotion | Fully approved thresholds from Step 2B-1B |
| v1.0-provisional-approved | Promotion | Conditionally approved thresholds |
| v1.0-mixed-governance | Promotion | Mixed approval states across KPIs |

---

## 2. Backup Policy

Before any active config promotion:

1. Copy current active config to `config/archive/`.
2. Name: `kpi_threshold_config_{previous_version}.csv`.
3. Record SHA-256 checksum.
4. Record timestamp.

---

## 3. Atomic Write

Promotion must be atomic:

1. Write new config to `kpi_threshold_config.csv.tmp`.
2. Verify temp file checksum.
3. Rename temp file to `kpi_threshold_config.csv`.
4. Verify final checksum.
5. Verify row count.

---

## 4. Rollback

If promotion must be reversed:

1. Locate backup in `config/archive/`.
2. Verify backup checksum matches recorded value.
3. Copy backup to active config path.
4. Verify restored checksum.
5. Record rollback audit entry.

---

## 5. Expiry and Review

- Approved thresholds may have an expiry date.
- Conditionally approved thresholds must have a required review date.
- Review dates trigger re-evaluation in future calibration cycles.
- Expired thresholds revert to Draft or Candidate status.
