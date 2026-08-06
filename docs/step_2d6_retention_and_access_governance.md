# Retention and Access Governance

## Overview

Phase 2D-6 classifies every record for retention and defines access role contracts. Retention periods are governed by configuration, not invented. Access roles are defined for future use; no authentication system is implemented.

## Retention Classification

Each record type receives a retention classification based on legal, regulatory, and operational requirements:

| Retention Class | Minimum Period | Basis |
|---|---|---|
| Permanent | Indefinite | Legislative or regulatory mandate |
| Long-Term | 10 years | Financial or clinical audit requirements |
| Medium-Term | 7 years | Standard operational audit trail |
| Short-Term | 3 years | Routine monitoring and review |
| Transient | 1 year | Temporary processing artefacts |

## Retention Rules

1. **No invented legal periods**: All retention periods are drawn from `config/decision_record_retention_config.csv`.
2. **Record-level classification**: Every output record is classified individually.
3. **Version retention**: Superseded versions retain the same retention class as current versions.
4. **Audit trail retention**: Audit event contracts are classified as Permanent.
5. **Issue register retention**: Evidence, lineage, and governance issues are classified as Long-Term.

## Retention Register

- Total retention classifications created: 12,274 records.
- Each retention record links to a specific output file and row.
- `retention_expiry_date` is calculated from `retention_period_years`.
- `legal_hold_flag` indicates whether the record is under active legal hold.

## Access Role Contracts

Access roles define who may view, modify, or approve records in a future system:

| Role | View | Modify | Approve | Notes |
|---|---|---|---|---|
| System Administrator | Yes | No | No | Read-only system access |
| Data Steward | Yes | Yes | No | Can update metadata and classifications |
| Clinical Auditor | Yes | No | No | Read-only clinical audit access |
| Financial Auditor | Yes | No | No | Read-only financial audit access |
| Governance Officer | Yes | Yes | No | Can update governance flags |
| Line Manager | Yes | No | No | Read-only management view |
| Senior Manager | Yes | No | Yes | Can approve actions |
| Executive Director | Yes | No | Yes | Can approve escalated actions |
| Compliance Officer | Yes | Yes | No | Can update compliance status |
| External Auditor | Yes | No | No | Time-limited read-only access |

## Access Governance Constraints

- **No authentication implemented**: User IDs and passwords are not created.
- **Role-based only**: Access is defined by role, not by individual.
- **Future-use contracts**: Access contracts are preparatory for a future identity system.
- **No access granted or revoked**: All access status fields are blank or set to "Pending System Integration".

## Output

- `step_2d6_retention_classification_register.csv` (12,274 rows)
- `step_2d6_access_role_contract.csv` (26 rows)
