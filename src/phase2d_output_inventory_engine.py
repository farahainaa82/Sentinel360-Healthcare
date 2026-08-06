"""Phase 2D output inventory engine."""
from phase2d_closure_utils import load_csv, compute_sha256
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "decision_intelligence"

def build_inventory():
    files = sorted(OUTPUT_DIR.glob("step_2d*.csv"))
    records = []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False, on_bad_lines="skip")
            records.append({
                "file_name": f.name,
                "row_count": len(df),
                "column_count": len(df.columns),
                "checksum": compute_sha256(f),
            })
        except Exception:
            pass
    return pd.DataFrame(records)

if __name__ == "__main__":
    print(build_inventory())
