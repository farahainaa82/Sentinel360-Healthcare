# Validation Rule Catalog

## Authority Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-001 | SHA-256 checksum verification | Critical |
| VR-002 | File existence and readability | Critical |

## Population Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-003 | Row count reconciliation (646 per 1:1 register) | Critical |

## Identity Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-004 | integrated_management_brief_id uniqueness | Critical |
| VR-005 | Foreign key integrity (decision_package_id, approval_package_id) | Critical |
| VR-006 | No Cartesian joins | Critical |

## Action Routing Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-011 | Approval status must remain Pending Management Review | Critical |
| VR-012 | selected_action must be blank | Critical |
| VR-013 | selected_scenario must be blank | Critical |

## KPI/Risk Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-007 | High/Critical risk not downgraded without attention | High |
| KR-001 | Critical Risk Escalation | High |
| KR-002 | High Risk Escalation | High |

## Financial Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-009 | Financial value immutability | High |

## Readiness Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-010 | Readiness status frozen | High |

## Evidence & Lineage Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-014 | Evidence completeness reconciliation | High |
| VR-015 | Lineage completeness reconciliation | High |

## Narrative Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-017 | One-line summary <= 40 words; short summary <= 130 words | Medium |

## Wording Governance Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-018 | No prohibited terms in issue_title | High |
| VR-019 | No unsupported causal language | High |

## Cross-Layer Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-021 | Logical consistency across layers | High |

## Audit Rules
| ID | Rule | Severity |
|----|------|----------|
| VR-016 | future_audit_status must be Awaiting Management Action | Medium |
