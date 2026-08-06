"""Phase 2D freeze engine."""
from phase2d_closure_utils import load_csv, compute_sha256
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "decision_intelligence"

def build_freeze_register():
    files = sorted(OUTPUT_DIR.glob("step_2d*.csv"))
    records = []
    for f in files:
        records.append({
            "file_name": f.name,
            "checksum": compute_sha256(f),
            "frozen_flag": True,
            "future_update_rule": "New governed version required",
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_freeze_register())
