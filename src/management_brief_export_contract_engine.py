"""Export contract engine for Step 2D-7."""

import pandas as pd


def create_export_contracts(briefs_df):
    """Create export-ready appendix contracts for each brief."""
    records = []
    export_types = [
        "One-Page Executive Brief",
        "Detailed Management Brief",
        "Scenario Comparison Appendix",
        "Financial Comparison Appendix",
        "Evidence Summary Appendix",
        "Lineage and Audit Appendix",
        "Monitoring Appendix",
        "Validation Requirements Appendix"
    ]
    for _, row in briefs_df.iterrows():
        brief_id = row.get("integrated_management_brief_id", "")
        for idx, exp_type in enumerate(export_types, 1):
            records.append({
                "integrated_management_brief_id": brief_id,
                "decision_package_id": row.get("decision_package_id", ""),
                "export_type": exp_type,
                "export_appendix": exp_type.replace(" Appendix", "").replace("One-Page ", ""),
                "display_order": idx,
                "available_flag": True,
                "governance_note": "Export contract for future generation"
            })
    return pd.DataFrame(records)
