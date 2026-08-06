"""Population validation to prevent Cartesian joins for Step 2D-7."""

from management_brief_utils import validate_no_cartesian


def validate_population_counts(dfs, key="decision_package_id", expected_count=646):
    """Validate that multiple DataFrames maintain expected unique key count."""
    for name, df in dfs.items():
        if key not in df.columns:
            raise KeyError(f"{name} missing key column {key}")
        actual = df[key].nunique()
        if actual != expected_count:
            raise ValueError(
                f"Population mismatch in {name}: expected {expected_count} {key}, got {actual}"
            )
    return True


def validate_join_shape(left, right, key, expected_multiplier=1):
    """Validate that a merge does not produce unexpected row multiplication."""
    import pandas as pd
    merged = pd.merge(left, right, on=key, how="left", suffixes=("", "_right"))
    expected = len(left) * expected_multiplier
    if len(merged) > expected * 1.1:
        raise ValueError(
            f"Join multiplication detected: expected ~{expected}, got {len(merged)}"
        )
    return merged
