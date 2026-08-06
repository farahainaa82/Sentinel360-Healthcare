"""Phase 2D superseded file engine."""
from phase2d_closure_utils import load_csv
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "decision_intelligence"

def build_superseded_register():
    backups = list(OUTPUT_DIR.glob("*.backup*"))
    records = []
    for f in backups:
        records.append({
            "file_name": f.name,
            "use_prohibited_flag": True,
            "governance_note": "Superseded by corrected version",
        })
    return pd.DataFrame(records) if records else pd.DataFrame(columns=["file_name","use_prohibited_flag","governance_note"])

if __name__ == "__main__":
    print(build_superseded_register())
