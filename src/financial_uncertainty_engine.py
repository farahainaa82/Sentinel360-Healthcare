"""
Financial Uncertainty Engine for Phase 2C-3.

Calculates low, central, and high financial estimates for scenario cost components
using governed assumption ranges.

Corrected join contract: accepts driver_mapping to enrich cost_components with
financial_input_id when the cost-component output does not already contain it.
"""

import os
import sys
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from financial_base_engine import FinancialBaseEngine


class FinancialUncertaintyEngine(FinancialBaseEngine):
    def __init__(self):
        super().__init__()

    def calculate_uncertainty(
        self,
        cost_components: pd.DataFrame,
        assumption_ranges: pd.DataFrame,
        driver_mapping: pd.DataFrame = None,
    ) -> pd.DataFrame:
        self.log("Calculating financial uncertainty with corrected schema contract...")
        if len(cost_components) == 0:
            return pd.DataFrame()

        df = cost_components.copy()

        # --- Schema-contract correction: enrich with financial_input_id ---
        if "financial_input_id" not in df.columns or df["financial_input_id"].isna().all():
            if driver_mapping is not None and len(driver_mapping) > 0:
                join_keys = ["scenario_run_id", "cost_component_name"]
                dm_cols = [c for c in ["scenario_run_id", "cost_component_name", "financial_input_id", "mapping_id", "unit"] if c in driver_mapping.columns]
                dm = driver_mapping[dm_cols].drop_duplicates(subset=join_keys)
                pre_len = len(df)
                df = df.merge(dm, on=join_keys, how="left")
                post_len = len(df)
                if post_len != pre_len:
                    self.log(
                        f"WARNING: Cartesian join detected. Rows changed from {pre_len} to {post_len}. "
                        "Blocking ambiguous mappings.",
                        level="warning",
                    )
                    # Flag ambiguous rows for blocking
                    dup_mask = df.duplicated(subset=join_keys, keep=False)
                    df.loc[dup_mask, "_ambiguous_mapping"] = True
                else:
                    df["_ambiguous_mapping"] = False
            else:
                self.log("WARNING: No driver_mapping provided and no financial_input_id in cost_components.")
                df["financial_input_id"] = ""
                df["_ambiguous_mapping"] = False
        else:
            df["_ambiguous_mapping"] = False

        # Build range lookup
        if len(assumption_ranges) == 0:
            self.log("WARNING: No assumption_ranges provided.")
            range_map = {}
            range_counts = pd.Series(dtype=int)
        else:
            range_map = assumption_ranges.set_index("financial_input_id").to_dict("index")
            range_counts = assumption_ranges["financial_input_id"].value_counts()

        records = []
        for _, row in df.iterrows():
            rec = self._assess_uncertainty(row, range_map, range_counts)
            records.append(rec)

        out_df = pd.DataFrame(records)
        eligible_count = (out_df["uncertainty_eligibility"] == "Eligible — Governed Range Available").sum()
        self.log(f"Uncertainty: {len(out_df)} total, {eligible_count} eligible.")
        return out_df

    def _assess_uncertainty(self, row, range_map, range_counts):
        scenario_run_id = row.get("scenario_run_id", "")
        approval_package_id = row.get("approval_package_id", "")
        scenario_family = row.get("scenario_family", "")
        comparator_type = row.get("comparator_type", "")
        cost_component_name = row.get("cost_component_name", "")
        financial_input_id = str(row.get("financial_input_id", "")) if pd.notna(row.get("financial_input_id")) else ""
        base_cost = row["component_cost"] if pd.notna(row.get("component_cost")) else None
        base_rate = row.get("rate_value", None)
        currency = row.get("currency", "MYR")
        cc_unit = str(row.get("unit", "")).strip()
        cc_currency = str(row.get("currency", "MYR")).strip().upper()

        # --- Ambiguous mapping block ---
        if row.get("_ambiguous_mapping", False):
            return self._build_record(
                scenario_run_id, approval_package_id, scenario_family, comparator_type,
                cost_component_name, financial_input_id, currency,
                eligibility="Blocked — Ambiguous Range Mapping",
                status="Blocked",
                governance_warning="Multiple driver_mapping rows matched the same cost component. Mapping not unique.",
                base_cost=base_cost, base_rate=base_rate,
            )

        # --- Missing financial input ---
        if financial_input_id == "":
            return self._build_record(
                scenario_run_id, approval_package_id, scenario_family, comparator_type,
                cost_component_name, financial_input_id, currency,
                eligibility="Ineligible — Missing Financial Input",
                status="Ineligible",
                governance_warning="No financial_input_id available for this cost component.",
                base_cost=base_cost, base_rate=base_rate,
            )

        # --- Missing governed range ---
        rng = range_map.get(financial_input_id, {})
        if not rng:
            return self._build_record(
                scenario_run_id, approval_package_id, scenario_family, comparator_type,
                cost_component_name, financial_input_id, currency,
                eligibility="Ineligible — No Governed Range",
                status="Ineligible",
                governance_warning=f"No assumption range found for {financial_input_id}.",
                base_cost=base_cost, base_rate=base_rate,
            )

        # --- Multiple active ranges block ---
        if financial_input_id in range_counts.index and range_counts[financial_input_id] > 1:
            return self._build_record(
                scenario_run_id, approval_package_id, scenario_family, comparator_type,
                cost_component_name, financial_input_id, currency,
                eligibility="Blocked — Multiple Active Ranges",
                status="Blocked",
                governance_warning=f"Multiple active ranges found for {financial_input_id}.",
                base_cost=base_cost, base_rate=base_rate,
                assumption_range_id=rng.get("range_id", ""),
            )

        # --- Unit mismatch check ---
        rng_currency = str(rng.get("currency_code", "")).strip().upper()
        rng_unit = str(rng.get("unit", "")).strip().lower()

        if rng_currency and cc_currency and rng_currency != cc_currency:
            return self._build_record(
                scenario_run_id, approval_package_id, scenario_family, comparator_type,
                cost_component_name, financial_input_id, currency,
                eligibility="Blocked — Unit Mismatch",
                status="Blocked",
                governance_warning=f"Currency mismatch: cost component {cc_currency} vs range {rng_currency}.",
                base_cost=base_cost, base_rate=base_rate,
                assumption_range_id=rng.get("range_id", ""),
            )

        # If cost component unit is a pure currency and range unit contains that currency, treat as compatible
        # Otherwise, if both have explicit non-currency units that differ, block
        if cc_unit and rng_unit and cc_currency not in rng_unit and cc_unit.lower() != rng_unit and rng_unit != "":
            # Additional check: if cc_unit is just a currency code and rng_unit is a rate unit containing it, OK
            if not (len(cc_unit) <= 3 and cc_unit.lower() in rng_unit):
                return self._build_record(
                    scenario_run_id, approval_package_id, scenario_family, comparator_type,
                    cost_component_name, financial_input_id, currency,
                    eligibility="Blocked — Unit Mismatch",
                    status="Blocked",
                    governance_warning=f"Unit mismatch: cost component '{cc_unit}' vs range '{rng_unit}'.",
                    base_cost=base_cost, base_rate=base_rate,
                    assumption_range_id=rng.get("range_id", ""),
                )

        # --- Not Applicable (zero base cost) ---
        if base_cost is not None and base_cost == 0:
            return self._build_record(
                scenario_run_id, approval_package_id, scenario_family, comparator_type,
                cost_component_name, financial_input_id, currency,
                eligibility="Ineligible — Not Applicable",
                status="Ineligible",
                governance_warning="Component cost is zero; no material uncertainty to quantify.",
                base_cost=base_cost, base_rate=base_rate,
                assumption_range_id=rng.get("range_id", ""),
            )

        # --- Actual Fixed Value (missing rate or non-rate-based cost) ---
        if base_rate is None or pd.isna(base_rate) or base_rate == 0:
            return self._build_record(
                scenario_run_id, approval_package_id, scenario_family, comparator_type,
                cost_component_name, financial_input_id, currency,
                eligibility="Ineligible — Actual Fixed Value",
                status="Ineligible",
                governance_warning="Base rate is zero or missing; cannot scale cost by governed rate range.",
                base_cost=base_cost, base_rate=base_rate,
                assumption_range_id=rng.get("range_id", ""),
            )

        # --- Eligible: calculate uncertainty ---
        low_rate = rng.get("default_low", rng.get("allowed_minimum"))
        high_rate = rng.get("default_high", rng.get("allowed_maximum"))
        central_rate = rng.get("default_central", rng.get("allowed_minimum"))

        # Defensive: ensure numeric
        try:
            low_rate_f = float(low_rate) if low_rate is not None else float(base_rate)
            high_rate_f = float(high_rate) if high_rate is not None else float(base_rate)
            central_rate_f = float(central_rate) if central_rate is not None else float(base_rate)
            base_rate_f = float(base_rate)
            base_cost_f = float(base_cost)
        except (ValueError, TypeError):
            return self._build_record(
                scenario_run_id, approval_package_id, scenario_family, comparator_type,
                cost_component_name, financial_input_id, currency,
                eligibility="Blocked — Rate Not Numeric",
                status="Blocked",
                governance_warning="Range or base rate values are non-numeric.",
                base_cost=base_cost, base_rate=base_rate,
                assumption_range_id=rng.get("range_id", ""),
            )

        # Scale cost proportionally to rate variation
        low_cost = base_cost_f * (low_rate_f / base_rate_f)
        high_cost = base_cost_f * (high_rate_f / base_rate_f)
        central_cost = base_cost_f  # central estimate is the original calculated cost

        range_width = high_cost - low_cost
        range_percentage = (range_width / central_cost * 100.0) if central_cost != 0 else None

        range_id = rng.get("range_id", "")
        range_source = rng.get("approval_status", "Draft Analytical Configuration")
        range_version = rng.get("configuration_version", "")
        governance_note = str(rng.get("governance_note", ""))

        stakeholder_required = True  # All ranges are Draft; stakeholder validation required

        return self._build_record(
            scenario_run_id, approval_package_id, scenario_family, comparator_type,
            cost_component_name, financial_input_id, currency,
            eligibility="Eligible — Governed Range Available",
            status="Calculated",
            governance_warning="",
            base_cost=base_cost, base_rate=base_rate,
            lower_estimate=low_cost,
            central_estimate=central_cost,
            upper_estimate=high_cost,
            range_width=range_width,
            range_percentage=range_percentage,
            primary_uncertainty_driver=financial_input_id,
            assumption_range_id=range_id,
            range_source=range_source,
            range_version=range_version,
            financial_input_status="Draft Analytical Assumption",
            stakeholder_validation_required=stakeholder_required,
            evidence=f"range_id={range_id}; low_rate={low_rate_f}; high_rate={high_rate_f}",
            lineage="financial_uncertainty_engine.py; config/financial_assumption_range.csv; step_2c3_cost_driver_mapping.csv",
        )

    def _build_record(
        self,
        scenario_run_id,
        approval_package_id,
        scenario_family,
        comparator_type,
        cost_component_name,
        financial_input_id,
        currency,
        eligibility,
        status,
        governance_warning,
        base_cost=None,
        base_rate=None,
        lower_estimate=None,
        central_estimate=None,
        upper_estimate=None,
        range_width=None,
        range_percentage=None,
        primary_uncertainty_driver=None,
        assumption_range_id=None,
        range_source=None,
        range_version=None,
        financial_input_status=None,
        stakeholder_validation_required=False,
        evidence=None,
        lineage=None,
    ):
        return {
            "scenario_run_id": scenario_run_id,
            "approval_package_id": approval_package_id,
            "scenario_family": scenario_family,
            "comparator_type": comparator_type,
            "cost_component_name": cost_component_name,
            "financial_input_id": financial_input_id,
            "base_cost": base_cost,
            "base_rate": base_rate,
            "lower_estimate": lower_estimate,
            "central_estimate": central_estimate,
            "upper_estimate": upper_estimate,
            "range_width": range_width,
            "range_percentage": range_percentage,
            "primary_uncertainty_driver": primary_uncertainty_driver,
            "assumption_range_id": assumption_range_id,
            "range_source": range_source,
            "range_version": range_version,
            "financial_input_status": financial_input_status,
            "uncertainty_eligibility": eligibility,
            "uncertainty_status": status,
            "stakeholder_validation_required": stakeholder_validation_required,
            "evidence": evidence,
            "lineage": lineage,
            "governance_warning": governance_warning,
            "currency": currency,
        }
