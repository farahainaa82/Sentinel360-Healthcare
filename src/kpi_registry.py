"""
Sentinel360 Healthcare — KPI Registry

Contains exactly the six approved KPIs with governed definitions.
No actual KPI calculation is performed in Step 2A-1.

Step: 2A-1
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from analytical_models import KPIDefinition


# ---------------------------------------------------------------------------
# 1. Approved KPI Definitions
# ---------------------------------------------------------------------------

_KPI_REGISTRY: Dict[str, KPIDefinition] = {}


def _register_kpi(kpi: KPIDefinition) -> None:
    _KPI_REGISTRY[kpi.kpi_id] = kpi


def build_registry_from_config(config_path) -> Dict[str, KPIDefinition]:
    """Build KPI registry from configuration directory or DataFrame."""
    registry: Dict[str, KPIDefinition] = {}
    import pandas as pd
    if isinstance(config_path, pd.DataFrame):
        config_df = config_path
    else:
        config_path = Path(config_path)
        config_file = config_path / "kpi_definition_config.csv"
        if not config_file.exists():
            return registry
        config_df = pd.read_csv(config_file)
    if config_df is None or config_df.empty:
        return registry

    for _, row in config_df.iterrows():
        kpi = KPIDefinition(
            kpi_id=str(row.get("kpi_id", "")),
            kpi_name=str(row.get("kpi_name", "")),
            domain=str(row.get("domain", "")),
            description=str(row.get("description", "")),
            numerator_definition=str(row.get("numerator_field", "")),
            denominator_definition=str(row.get("denominator_field", "")),
            formula_text=str(row.get("formula_text", "")),
            unit=str(row.get("unit", "")),
            directionality=str(row.get("directionality", "")),
            grain=str(row.get("grain", "")),
            calculation_frequency=str(row.get("calculation_frequency", "")),
            authoritative_input_dataset=str(row.get("source_dataset", "")),
            required_fields=_parse_list(row.get("required_fields", "")),
            eligibility_rules=_parse_list(row.get("eligibility_rules", "")),
            exclusion_rules=_parse_list(row.get("exclusion_rules", "")),
            null_treatment=str(row.get("null_treatment", "")),
            zero_denominator_treatment=str(row.get("zero_denominator_treatment", "")),
            minimum_denominator=_parse_float(row.get("minimum_denominator")),
            threshold_config_reference=str(row.get("threshold_config_reference", "")),
            data_confidence_rule_reference=str(row.get("data_confidence_rule_reference", "")),
            config_version=str(row.get("config_version", "")),
            approval_requirement=str(row.get("approval_requirement", "")),
            readiness_status="Not Applicable",
            unresolved_rules=_parse_list(row.get("unresolved_rules", "")),
            effective_date=row.get("effective_date"),
            approval_status=str(row.get("approval_status", "")),
        )
        registry[kpi.kpi_id] = kpi

    return registry


def _parse_list(value: Any) -> List[str]:
    if pd.isna(value) or value is None or value == "":
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    if isinstance(value, list):
        return [str(v).strip() for v in value if pd.notna(v) and str(v).strip()]
    return []


def _parse_float(value: Any) -> Optional[float]:
    if pd.isna(value) or value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 2. Registry API
# ---------------------------------------------------------------------------

class KPIRegistry:
    """Governed registry of approved KPIs."""

    def __init__(self, registry: Optional[Dict[str, KPIDefinition]] = None):
        self._registry = registry or {}

    def get_kpi(self, kpi_id: str) -> Optional[KPIDefinition]:
        return self._registry.get(kpi_id)

    def list_kpi_ids(self) -> List[str]:
        return sorted(self._registry.keys())

    def list_kpis(self) -> List[KPIDefinition]:
        return list(self._registry.values())

    def validate_completeness(self) -> Dict[str, Any]:
        """Validate that exactly six approved KPIs are registered."""
        approved_names = {
            "Staffing Level",
            "Staff Absenteeism Rate",
            "Bed Occupancy Rate",
            "Average Patient Waiting Time",
            "Patient Complaint Rate",
            "Patient Satisfaction Score",
        }
        registered_names = {kpi.kpi_name for kpi in self._registry.values()}

        missing = approved_names - registered_names
        extra = registered_names - approved_names

        return {
            "total_registered": len(self._registry),
            "approved_expected": 6,
            "missing": sorted(missing),
            "extra": sorted(extra),
            "valid": len(missing) == 0 and len(extra) == 0 and len(self._registry) == 6,
        }

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        return {kpi_id: kpi.to_dict() for kpi_id, kpi in self._registry.items()}


# ---------------------------------------------------------------------------
# 3. Lazy import for pandas
# ---------------------------------------------------------------------------

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore
