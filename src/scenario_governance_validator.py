"""Scenario governance validator.

Phase 2C-2C — Validates assumptions and enforces governance rules before scenario calculation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.scenario_models import AssumptionValidation, ValidationOutcome
from src.scenario_config_loader import ScenarioConfigLoader


class ScenarioGovernanceValidator:
    """Validates assumptions against configured ranges and governance rules."""

    def __init__(self, loader: ScenarioConfigLoader):
        self.loader = loader
        self._range_cache: Dict[str, Dict[str, Any]] = {}
        self._governance_cache: Dict[str, List[Dict[str, Any]]] = {}

    def validate_assumptions(
        self, assumptions: Dict[str, Any], family: str
    ) -> Tuple[List[AssumptionValidation], bool]:
        """Validate all assumptions in a profile. Returns validations and all_valid flag."""
        validations: List[AssumptionValidation] = []
        all_valid = True

        for assumption_id, raw_value in assumptions.items():
            validation = self._validate_single_assumption(assumption_id, raw_value, family)
            validations.append(validation)
            if validation.validation_outcome in (ValidationOutcome.INVALID, ValidationOutcome.BLOCKED, ValidationOutcome.MISSING):
                all_valid = False

        return validations, all_valid

    def _validate_single_assumption(
        self, assumption_id: str, raw_value: Any, family: str
    ) -> AssumptionValidation:
        """Validate a single assumption value."""
        # Check for missing required values
        if raw_value is None or str(raw_value).strip() == "":
            range_config = self._get_range_config(assumption_id)
            if range_config and str(range_config.get("required_flag", "")).lower() == "true":
                return AssumptionValidation(
                    assumption_id=assumption_id,
                    assumption_name=assumption_id,
                    original_value=raw_value,
                    validated_value=None,
                    validation_outcome=ValidationOutcome.MISSING,
                    validation_message="Required assumption is missing.",
                )
            else:
                return AssumptionValidation(
                    assumption_id=assumption_id,
                    assumption_name=assumption_id,
                    original_value=raw_value,
                    validated_value=raw_value,
                    validation_outcome=ValidationOutcome.VALID,
                    validation_message="Optional assumption is missing; ignored.",
                )

        # Convert to float if possible
        try:
            float_value = float(str(raw_value).strip())
            is_numeric = True
        except (ValueError, TypeError):
            float_value = None
            is_numeric = False

        range_config = self._get_range_config(assumption_id)
        if range_config is None:
            # No range config found; pass through with warning
            return AssumptionValidation(
                assumption_id=assumption_id,
                assumption_name=assumption_id,
                original_value=raw_value,
                validated_value=raw_value,
                validation_outcome=ValidationOutcome.VALID,
                validation_message="No range configuration found; assumption accepted without validation.",
            )

        data_type = str(range_config.get("data_type", "float")).lower()
        if data_type == "float" and not is_numeric:
            return AssumptionValidation(
                assumption_id=assumption_id,
                assumption_name=assumption_id,
                original_value=raw_value,
                validated_value=raw_value,
                validation_outcome=ValidationOutcome.INVALID,
                validation_message=f"Expected numeric value; got '{raw_value}'.",
                hard_limit_violated=True,
            )

        min_allowed = _to_float_or_none(range_config.get("minimum_allowed"))
        max_allowed = _to_float_or_none(range_config.get("maximum_allowed"))
        hard_limit_min = _to_float_or_none(range_config.get("hard_limit_min"))
        hard_limit_max = _to_float_or_none(range_config.get("hard_limit_max"))
        soft_limit_min = _to_float_or_none(range_config.get("soft_limit_min"))
        soft_limit_max = _to_float_or_none(range_config.get("soft_limit_max"))
        default_value = _to_float_or_none(range_config.get("default_value"))

        validated_value = float_value if is_numeric else raw_value
        adjustment = "None"

        # Check hard limits
        if is_numeric and hard_limit_min is not None and float_value < hard_limit_min:
            return AssumptionValidation(
                assumption_id=assumption_id,
                assumption_name=assumption_id,
                original_value=raw_value,
                validated_value=validated_value,
                validation_outcome=ValidationOutcome.INVALID,
                validation_message=f"Value {float_value} below hard limit {hard_limit_min}.",
                hard_limit_violated=True,
                adjustment_applied="None",
            )
        if is_numeric and hard_limit_max is not None and float_value > hard_limit_max:
            return AssumptionValidation(
                assumption_id=assumption_id,
                assumption_name=assumption_id,
                original_value=raw_value,
                validated_value=validated_value,
                validation_outcome=ValidationOutcome.INVALID,
                validation_message=f"Value {float_value} exceeds hard limit {hard_limit_max}.",
                hard_limit_violated=True,
                adjustment_applied="None",
            )

        # Check soft limits
        soft_violated = False
        soft_message = ""
        if is_numeric and soft_limit_min is not None and float_value < soft_limit_min:
            soft_violated = True
            soft_message = f"Value {float_value} below soft limit {soft_limit_min}. "
        if is_numeric and soft_limit_max is not None and float_value > soft_limit_max:
            soft_violated = True
            soft_message += f"Value {float_value} exceeds soft limit {soft_limit_max}. "

        # Check allowed range
        if is_numeric and min_allowed is not None and float_value < min_allowed:
            soft_violated = True
            soft_message += f"Value {float_value} below minimum allowed {min_allowed}. "
        if is_numeric and max_allowed is not None and float_value > max_allowed:
            soft_violated = True
            soft_message += f"Value {float_value} exceeds maximum allowed {max_allowed}. "

        if soft_violated:
            return AssumptionValidation(
                assumption_id=assumption_id,
                assumption_name=assumption_id,
                original_value=raw_value,
                validated_value=validated_value,
                validation_outcome=ValidationOutcome.VALID_WITH_WARNING,
                validation_message=soft_message.strip(),
                soft_limit_violated=True,
            )

        return AssumptionValidation(
            assumption_id=assumption_id,
            assumption_name=assumption_id,
            original_value=raw_value,
            validated_value=validated_value,
            validation_outcome=ValidationOutcome.VALID,
            validation_message="Valid.",
        )

    def _get_range_config(self, assumption_id: str) -> Optional[Dict[str, Any]]:
        if assumption_id not in self._range_cache:
            self._range_cache[assumption_id] = self.loader.get_assumption_ranges(assumption_id)
        return self._range_cache[assumption_id]

    def get_governance_rules_for_template(self, template_id: str) -> List[Dict[str, Any]]:
        if template_id not in self._governance_cache:
            self._governance_cache[template_id] = self.loader.get_governance_rules_for_template(template_id)
        return self._governance_cache[template_id]

    def check_governance_rules(
        self, baseline: Any, assumptions: Dict[str, Any], template_id: str
    ) -> List[Tuple[str, str, bool]]:
        """Check governance rules. Returns list of (rule_id, message, passed)."""
        rules = self.get_governance_rules_for_template(template_id)
        results = []
        for rule in rules:
            rule_id = rule.get("rule_id", "")
            rule_name = rule.get("rule_name", "")
            condition_type = rule.get("condition_type", "")
            threshold_value = rule.get("threshold_value", "")
            action = rule.get("action", "")

            passed = True
            message = f"Rule {rule_name}: passed"

            if condition_type == "baseline_complete" and threshold_value:
                req = float(threshold_value) if str(threshold_value).replace(".", "", 1).isdigit() else 0.0
                if baseline.baseline_data_completeness < req:
                    passed = False
                    message = f"Rule {rule_name}: baseline completeness {baseline.baseline_data_completeness:.1f}% below threshold {req}%"
            elif condition_type == "missing_critical_assumption":
                critical = ["additional_staff_count", "assumed_absenteeism_reduction_pct", "arrival_change_pct"]
                missing = [a for a in critical if a not in assumptions or assumptions[a] is None]
                if missing:
                    passed = False
                    message = f"Rule {rule_name}: missing critical assumptions {missing}"
            elif condition_type == "provisional_threshold":
                if baseline.baseline_provisional_flag:
                    passed = False
                    message = f"Rule {rule_name}: baseline uses provisional threshold; {action}"
            elif condition_type == "contradiction_major":
                if baseline.baseline_contradiction_severity == "Major":
                    passed = False
                    message = f"Rule {rule_name}: major contradiction detected; execution blocked"

            results.append((rule_id, message, passed))
        return results


def _to_float_or_none(val: Any) -> Optional[float]:
    if val is None or str(val).strip() == "":
        return None
    try:
        f = float(str(val).strip())
        if pd.isna(f):
            return None
        return f
    except (ValueError, TypeError):
        return None
