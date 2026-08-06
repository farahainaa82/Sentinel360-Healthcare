"""
Financial Governance Validator for Phase 2C-3.

Validates outputs against display governance rules and prohibited wording.
"""

import pandas as pd
from financial_base_engine import FinancialBaseEngine


class FinancialGovernanceValidator(FinancialBaseEngine):
    def __init__(self):
        super().__init__()
        self.prohibited_words = [
            "guaranteed savings", "proven roi", "best financial option", "optimal investment",
            "certain benefit", "approved budget", "will save", "will generate",
            "financially recommended scenario", "high confidence",
        ]

    def validate_outputs(self, outputs_dict: dict) -> pd.DataFrame:
        self.log("Validating financial governance...")
        issues = []

        for out_name, df in outputs_dict.items():
            if df is None or len(df) == 0:
                continue
            text = df.to_string().lower()
            for word in self.prohibited_words:
                if word in text:
                    issues.append({
                        "issue_id": f"GOV-{out_name}-{word.replace(' ', '')[:20]}",
                        "output_file": out_name,
                        "issue_type": "Prohibited Wording",
                        "description": f"Prohibited phrase '{word}' detected in {out_name}",
                        "severity": "High",
                        "governance_warning": "Remove or rephrase prohibited wording",
                    })

        df = pd.DataFrame(issues)
        self.log(f"Governance validation: {len(df)} issues.")
        return df
