"""Brief type mapping engine for Step 2D-7."""

from management_brief_utils import load_csv


def map_brief_type(readiness_status, config_path=None):
    """Map a readiness status to a brief type."""
    if config_path is None:
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config", "management_brief_type_config.csv"
        )
    cfg = load_csv(config_path)
    mask = cfg["readiness_status"] == readiness_status
    if mask.any():
        return cfg.loc[mask, "brief_type"].iloc[0]
    return "Integrated Management Review Brief"


def assign_brief_types(briefs_df, config_path=None):
    """Assign brief_type to all briefs based on readiness_status."""
    briefs_df = briefs_df.copy()
    briefs_df["brief_type"] = briefs_df["final_readiness_status"].apply(
        lambda x: map_brief_type(x, config_path)
    )
    return briefs_df
