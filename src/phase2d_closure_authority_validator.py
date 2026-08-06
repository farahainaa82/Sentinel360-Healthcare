"""Phase 2D-9 authority validator."""
from phase2d_closure_utils import load_csv, compute_sha256
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "decision_intelligence"

def validate_authority():
    required = [
        "step_2d7_integrated_management_brief_register.csv",
        "step_2d8_master_validation_register.csv",
        "step_2d8_final_validation_outcome_register.csv",
    ]
    results = []
    for f in required:
        path = OUTPUT_DIR / f
        exists = path.exists()
        checksum = compute_sha256(path) if exists else ""
        results.append({"file": f, "exists": exists, "checksum": checksum})
    return pd.DataFrame(results)

if __name__ == "__main__":
    print(validate_authority())
