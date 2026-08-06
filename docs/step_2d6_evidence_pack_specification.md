# Evidence Pack Specification

## Overview

An evidence pack is a structured collection of all evidence, lineage, audit, and governance records pertaining to a single decision package. Phase 2D-6 creates evidence pack contracts that define which sections must be present for a pack to be considered complete.

## Evidence Pack Sections

Each evidence pack must contain the following sections:

| Section | Required | Description |
|---|---|---|
| Evidence Profile | Yes | Summary of evidence categories and completeness |
| Evidence References | Yes | Detailed references to all 28 evidence categories |
| Evidence Completeness | Yes | Assessment of evidence gaps and conditions |
| Lineage Profile | Yes | Summary of lineage stages and completeness |
| Lineage Links | Yes | Detailed parent-child links for all 18 stages |
| Lineage Completeness | Yes | Assessment of lineage gaps and orphans |
| Source-to-Decision Trace | Yes | Verifiable path from source to decision |
| Audit Requirements | Yes | Integrated audit requirements from 2D-5 |
| Audit Event Contracts | Yes | All "Not Executed" audit event contracts |
| Decision History | Yes | Historical state and version information |
| Version Control | Yes | Version status of all authoritative inputs |
| Integrity Check | Yes | SHA-256 checksum verification results |
| Retention Classification | Yes | Retention class and expiry for all records |
| Access Role Contract | Yes | Defined roles for future access control |
| Management Review Contract | Yes | Pending management review status |
| Audit Explanation | Yes | Human-readable audit explanation |
| Streamlit Data Contract | Yes | UI-ready data fields for future display |

## Completeness Assessment

- `required_section_count`: 17 (all sections required)
- `present_section_count`: Sections with at least one record
- `missing_section_count`: 17 - present
- `pack_completeness_status`: Complete if all 17 present; otherwise Incomplete

## Missing Section Visibility

- Missing sections are explicitly listed per pack.
- Missing sections do not block pack creation; they are flagged for management attention.
- Governance note explains which sections are absent and why.

## Governance

- Evidence packs are created for every decision package (646 packs).
- No pack is fabricated for a non-existent decision.
- Pack contents are read-only after creation.
- Superseded packs are flagged, not deleted.

## Output

- `step_2d6_evidence_pack_contract.csv` (11,628 rows)
