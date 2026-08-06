"""Phase 2D population reconciliation engine."""
from phase2d_closure_utils import load_csv
import pandas as pd

def reconcile_populations():
    imb = load_csv("step_2d7_integrated_management_brief_register.csv")
    populations = [
        ("management_briefs", 646, len(imb)),
        ("validation_profiles", 646, len(load_csv("step_2d8_master_validation_register.csv"))),
    ]
    records = []
    for name, expected, actual in populations:
        records.append({
            "population_name": name,
            "expected_count": expected,
            "actual_count": actual,
            "reconciled_flag": expected == actual,
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(reconcile_populations())
