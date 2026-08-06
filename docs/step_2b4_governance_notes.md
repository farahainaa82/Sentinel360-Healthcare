# Step 2B-4 Governance Notes

**Scope:** Relationship and Contributing-Factor Analysis  
**Date:** 2026-07-28  
**Status:** Active

---

## 1. Non-Causality Governance

Step 2B-4 analyses statistical associations, temporal precedences, and trend alignments. It **does not** establish causation.

### Required Labels

| Context | Required Language |
|---------|-------------------|
| Hypothesis records | "Potential Root-Cause Hypothesis — Not Confirmed" |
| Causality status field | "Not Confirmed" |
| Evidence records | "Association found" (not "Caused by") |
| Network edges | "Relationship" (not "Causal link") |

### Prohibited Language

The following terms are **forbidden** in all Step 2B-4 outputs:

- "Caused"
- "Root cause confirmed"
- "Causality proven"
- "Deterministic effect"
- "Direct cause"

The `RelationshipEvidenceEngine` validates all generated text against a prohibited-word list and raises `ValueError` if any are detected.

---

## 2. Confidence Model

Contributing-factor relationships are assigned one of four confidence levels:

| Level | Criteria |
|-------|----------|
| **High** | >= 100 paired observations, p < 0.01, stable across departments |
| **Moderate** | >= 60 paired observations, p < 0.05, mostly stable |
| **Low** | >= 30 paired observations, p < 0.10, mixed stability |
| **Insufficient Evidence** | < 30 observations or fewer than 3 components available |

Confidence is computed by the `KPIRelationshipAnalysisEngine` and carried forward into contributing-factor scoring.

---

## 3. Contradiction Severity Model

Contradictions downgrade contributing-factor classifications and may prevent Strong Hypothesis designation.

| Severity | Conditions | Penalty | Impact on Classification |
|----------|------------|---------|--------------------------|
| **None** | No contradictions detected | 0 | Standard scoring |
| **Minor** | Single mild contradiction (opposite trend, limited observations) | 5 | Standard scoring |
| **Material** | Moderate contradiction (opposite direction, pooled vs dept mismatch, reversed precedence) | 15 | Standard scoring |
| **Major** | Severe pooled-dept mismatch + strong reversed precedence | 35 | Caps at Weak Association |

**Key rule:** A Major contradiction prevents any relationship from being classified as "Strong Contributing-Factor Hypothesis", regardless of score.

---

## 4. Provisional KPI Governance

Provisional KPIs (currently `kpi_003`, `kpi_005`) receive a 0.92 governance multiplier on contributing-factor scores. Provisional relationships are flagged in:

- `provisional_relationship_flag`
- `provisional_kpi_list`
- `provisional_contribution_materiality`

Hypotheses involving provisional KPIs carry the additional warning:

> "Potential Root-Cause Hypothesis — Not Confirmed"

---

## 5. Hypothesis Eligibility Rules

Potential root-cause hypotheses are generated **only** for:

- Departments in **High** or **Critical** priority tiers
- Relationships with contributing-factor score >= 50.0
- Relationships with confidence >= Moderate
- Relationships **without** Major contradiction severity
- Relationships where the dominant KPI is either source or target

All hypotheses require `stakeholder_validation_required = True`.

---

## 6. Network Edge Governance

The relationship network (`analytical_relationship_network_edges.csv`) contains 15 edges (one per undirected KPI pair). Edges are directed based on the stronger temporal-precedence direction.

- `active_edge_flag` is True only when `contributing_factor_score_normalized > 20`
- Inactive edges remain in the dataset for audit completeness
- Pooled (ALL-grain) records are preferred over department averages when both exist

---

## 7. Audit and Lineage

Every Step 2B-4 output carries:

- `engine_run_id` — unique run identifier
- `processed_at` — ISO-8601 timestamp
- `relationship_id` — links back to source pair configuration
- `evidence_pack_id` — groups evidence for stakeholder review

Lineage records trace each output row back to its source datasets (daily KPI files, department risk files, threshold configs).

---

## 8. Technical Debt

1. **Time stability component placeholder** — Fixed at 50 until time-window stability is fully implemented.
2. **Best-supported lag placeholder** — Fixed at 0 until lag-selection heuristics are refined.
3. **Legacy NaN scores** — 102 of 135 records in the existing `analytical_contributing_factor_scores.csv` have NaN scores because an earlier engine version left scores as None when components were missing. Current engine code always computes numeric scores. Regeneration deferred to user discretion.

---

## 9. Sign-Off

| Role | Status |
|------|--------|
| Non-causality governance | Enforced |
| Confidence model | Implemented |
| Contradiction severity | Fixed and validated |
| Provisional KPI rules | Implemented |
| Hypothesis eligibility | Implemented |
| Audit lineage | Complete |
