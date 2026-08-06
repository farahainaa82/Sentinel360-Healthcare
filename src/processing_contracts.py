"""
Sentinel360 Healthcare — Processing Contracts

Defines processing contracts, interfaces and the validation gate.
No actual data transformation is performed in Step 2D-1.

Step: 2D-1
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# 1. ValidationGateContract
# ---------------------------------------------------------------------------

@dataclass
class ValidationGateResult:
    """Result of evaluating the validation gate."""

    processing_allowed: bool = False
    blocking_reason: str = ""
    accepted_datasets: List[str] = field(default_factory=list)
    excluded_datasets: List[str] = field(default_factory=list)
    validation_run_id: str = ""
    manual_override_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processing_allowed": self.processing_allowed,
            "blocking_reason": self.blocking_reason,
            "accepted_datasets": self.accepted_datasets,
            "excluded_datasets": self.excluded_datasets,
            "validation_run_id": self.validation_run_id,
            "manual_override_applied": self.manual_override_applied,
        }


class ValidationGateContract:
    """Contract that determines whether processing is permitted based on validation results.

    Processing is allowed only when:
      - run_status is "Passed" or "Passed with Warnings", AND
      - processing_allowed_flag is true.

    Manual overrides are not automatically applied in Step 2D-1.
    """

    @staticmethod
    def check_validation_gate(
        validation_manifest: Dict[str, Any],
        dataset_summary: Optional[pd.DataFrame] = None,
        override_register: Optional[pd.DataFrame] = None,
    ) -> ValidationGateResult:
        """Evaluate whether processing is allowed.

        Args:
            validation_manifest: The validation_run_manifest.json loaded as dict.
            dataset_summary: Optional DataFrame of dataset_validation_summary.csv.
            override_register: Optional DataFrame of manual_override_register.csv.

        Returns:
            ValidationGateResult with processing_allowed and supporting detail.
        """
        result = ValidationGateResult()
        result.validation_run_id = validation_manifest.get("validation_run_id", "")

        run_status = validation_manifest.get("run_status", "")
        processing_allowed_flag = validation_manifest.get("processing_allowed_flag", False)

        if run_status in ("Failed", "Blocked"):
            result.blocking_reason = f"Validation run status is '{run_status}'. Processing blocked."
            result.processing_allowed = False
            return result

        if not processing_allowed_flag:
            result.blocking_reason = "Validation manifest reports processing_allowed_flag = false."
            result.processing_allowed = False
            return result

        if run_status not in ("Passed", "Passed with Warnings"):
            result.blocking_reason = f"Unexpected validation run status '{run_status}'."
            result.processing_allowed = False
            return result

        # Determine accepted datasets from summary
        accepted: List[str] = []
        excluded: List[str] = []
        if dataset_summary is not None and "dataset_name" in dataset_summary.columns:
            for _, row in dataset_summary.iterrows():
                ds_name = str(row["dataset_name"])
                ds_status = str(row.get("dataset_status", ""))
                if ds_status in ("Valid", "Valid with Warnings"):
                    accepted.append(ds_name)
                else:
                    excluded.append(ds_name)

        result.processing_allowed = True
        result.blocking_reason = ""
        result.accepted_datasets = accepted
        result.excluded_datasets = excluded
        return result


# ---------------------------------------------------------------------------
# 2. SourceToProcessedContract
# ---------------------------------------------------------------------------

@dataclass
class SourceToProcessedContract:
    """Contract mapping a source dataset to its processed output."""

    source_dataset_name: str
    processed_dataset_name: str
    transformation_step: str
    source_primary_key: str
    processed_primary_key: str
    required_configuration: List[str] = field(default_factory=list)
    exclusion_behaviour: str = "Exclude with reason"
    lineage_required: bool = True
    output_grain: str = ""
    downstream_consumers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_dataset_name": self.source_dataset_name,
            "processed_dataset_name": self.processed_dataset_name,
            "transformation_step": self.transformation_step,
            "source_primary_key": self.source_primary_key,
            "processed_primary_key": self.processed_primary_key,
            "required_configuration": self.required_configuration,
            "exclusion_behaviour": self.exclusion_behaviour,
            "lineage_required": self.lineage_required,
            "output_grain": self.output_grain,
            "downstream_consumers": self.downstream_consumers,
        }


# ---------------------------------------------------------------------------
# 3. TransformationResultContract
# ---------------------------------------------------------------------------

@dataclass
class TransformationResultContract:
    """Result container for a single dataset transformation."""

    processed_dataframe: Optional[pd.DataFrame] = None
    lineage_dataframe: Optional[pd.DataFrame] = None
    exclusion_dataframe: Optional[pd.DataFrame] = None
    issues: List[Any] = field(default_factory=list)
    dataset_result: Optional[Any] = None
    success_flag: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processed_rows": len(self.processed_dataframe) if self.processed_dataframe is not None else 0,
            "lineage_rows": len(self.lineage_dataframe) if self.lineage_dataframe is not None else 0,
            "exclusion_rows": len(self.exclusion_dataframe) if self.exclusion_dataframe is not None else 0,
            "issue_count": len(self.issues),
            "success_flag": self.success_flag,
        }


# ---------------------------------------------------------------------------
# 4. ProcessingEngineContract (Abstract)
# ---------------------------------------------------------------------------

class ProcessingEngineContract(ABC):
    """Abstract contract for the future processing engine.

    Step 2D-1 defines the interface only.
    Implementation will follow in Steps 2D-2 through 2D-5.
    """

    @abstractmethod
    def check_validation_gate(self, validation_manifest: Dict[str, Any]) -> ValidationGateResult:
        """Evaluate whether processing is permitted."""
        ...

    @abstractmethod
    def load_source_data(self, dataset_name: str, input_directory: Path) -> pd.DataFrame:
        """Load a validated source dataset."""
        ...

    @abstractmethod
    def transform_dataset(
        self,
        source_df: pd.DataFrame,
        source_dataset_name: str,
        processed_dataset_name: str,
    ) -> TransformationResultContract:
        """Transform a source dataset into its processed form."""
        ...

    @abstractmethod
    def validate_processed_schema(
        self,
        processed_df: pd.DataFrame,
        processed_dataset_name: str,
    ) -> List[str]:
        """Validate that a processed dataframe conforms to its schema."""
        ...

    @abstractmethod
    def build_lineage(
        self,
        source_df: pd.DataFrame,
        processed_df: pd.DataFrame,
        transformation_rule_id: str,
    ) -> pd.DataFrame:
        """Build lineage records linking source to processed."""
        ...

    @abstractmethod
    def build_exclusions(
        self,
        source_df: pd.DataFrame,
        exclusion_reasons: Dict[str, str],
    ) -> pd.DataFrame:
        """Build exclusion register records."""
        ...

    @abstractmethod
    def export_processed_dataset(
        self,
        processed_df: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Export a processed dataset to CSV."""
        ...

    @abstractmethod
    def build_processing_manifest(self) -> Dict[str, Any]:
        """Build the processing run manifest."""
        ...
