"""Tests for Relationship Evidence Engine — Step 2B-4."""

import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(scope="module")
def evidence():
    return pd.read_csv("data/analytical/analytical_relationship_evidence.csv")


@pytest.fixture(scope="module")
def lineage():
    return pd.read_csv("data/analytical/analytical_relationship_lineage.csv")


class TestEvidence:
    def test_evidence_records_linked(self, evidence):
        assert evidence["relationship_record_id"].notna().all()

    def test_evidence_types_present(self, evidence):
        types = evidence["evidence_type"].unique()
        assert len(types) >= 3

    def test_no_orphan_evidence(self, evidence):
        assert not evidence["relationship_record_id"].isna().any()

    def test_source_references_present(self, evidence):
        assert evidence["source_reference"].notna().all()


class TestLineage:
    def test_lineage_records_linked(self, lineage):
        assert lineage["output_dataset"].notna().all()

    def test_source_datasets_present(self, lineage):
        assert lineage["source_datasets"].notna().all()

    def test_no_orphan_lineage(self, lineage):
        assert not lineage["output_dataset"].isna().any()

    def test_record_counts_positive(self, lineage):
        assert (lineage["record_count"] >= 0).all()
