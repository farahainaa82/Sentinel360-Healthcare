"""Shared utilities for Step 2D-7 Integrated Management Brief."""

import os
import hashlib
import shutil
import time
import json
from datetime import datetime

import pandas as pd


def load_csv(path, **kwargs):
    """Load a CSV file, returning empty DataFrame if missing or empty."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame()
    opts = {"low_memory": False, "on_bad_lines": "skip"}
    opts.update(kwargs)
    try:
        return pd.read_csv(path, **opts)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    except Exception:
        fallback = {"on_bad_lines": "skip", "engine": "python"}
        fallback.update({k: v for k, v in kwargs.items() if k != "low_memory"})
        try:
            return pd.read_csv(path, **fallback)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()


def compute_sha256(filepath):
    """Compute SHA-256 hex digest for a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_tmp_dir(tmp_dir):
    """Create tmp directory; clean if exists."""
    if os.path.exists(tmp_dir):
        for _ in range(5):
            try:
                shutil.rmtree(tmp_dir)
                break
            except PermissionError:
                time.sleep(0.5)
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir


def atomic_write(df, tmp_path, final_path):
    """Write DataFrame to tmp path, then move atomically to final path."""
    df.to_csv(tmp_path, index=False)
    if os.path.exists(final_path):
        os.remove(final_path)
    shutil.move(tmp_path, final_path)


def acquire_lock(lock_file, step_name):
    """Acquire execution lock or raise if already running."""
    if os.path.exists(lock_file):
        with open(lock_file, "r") as f:
            content = f.read().strip()
        if content and not any(s in content for s in ("COMPLETED", "CLEARED", "FAILED")):
            raise RuntimeError(f"Lock active: {content}")
    with open(lock_file, "w") as f:
        f.write(f"{step_name} RUNNING {datetime.now().isoformat()}")


def release_lock(lock_file, step_name):
    """Release execution lock with completed status."""
    with open(lock_file, "w") as f:
        f.write(f"{step_name} COMPLETED {datetime.now().isoformat()}")


def log_progress(logger, stage, start_time):
    """Log elapsed time for a stage."""
    elapsed = time.time() - start_time
    msg = f"Stage: {stage} | Elapsed: {elapsed:.3f}s"
    logger.append(msg)
    print(msg)
    return elapsed


def validate_no_cartesian(df, expected_key, expected_count):
    """Validate that a join did not produce unexpected multiplication."""
    actual = df[expected_key].nunique()
    if actual != expected_count:
        raise ValueError(
            f"Cartesian join detected: expected {expected_count} unique {expected_key}, got {actual}"
        )


def generate_manifest(output_dir, outputs, step_name, mode="full_run"):
    """Generate JSON manifest for all outputs."""
    manifest = {
        "step": step_name,
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "status": "COMPLETE",
        "outputs": {}
    }
    for name, path in outputs.items():
        if os.path.exists(path):
            manifest["outputs"][name] = {
                "path": path,
                "checksum": compute_sha256(path),
                "rows": len(load_csv(path)),
                "columns": len(load_csv(path).columns) if len(load_csv(path)) > 0 else 0
            }
    manifest_path = os.path.join(output_dir, f"{step_name.lower()}_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def build_execution_summary(logger, step_name, mode="full_run"):
    """Build execution summary DataFrame."""
    records = []
    for entry in logger:
        if "Stage:" in entry:
            parts = entry.split("|")
            stage = parts[0].replace("Stage:", "").strip()
            elapsed = float(parts[1].replace("Elapsed:", "").replace("s", "").strip())
            records.append({
                "stage": stage,
                "elapsed_seconds": elapsed,
                "timestamp": datetime.now().isoformat()
            })
    if records:
        total = sum(r["elapsed_seconds"] for r in records)
        records.append({"stage": "total_execution", "elapsed_seconds": total, "timestamp": datetime.now().isoformat()})
    df = pd.DataFrame(records)
    df["step"] = step_name
    df["mode"] = mode
    df["status"] = "COMPLETE" if records else "FAILED"
    return df
