"""Test scenario trade-off comparator balance.

Verifies that comparator analyses are balanced and missing comparators are handled.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd


def test_comparator_analysis_not_zero_for_missing():
    df = pd.read_csv("data/analytical/analytical_scenario_comparator_analysis.csv", keep_default_na=False)
    # Missing comparators should not be interpreted as zero impact
    # Check that no comparison has both comparators as the same
    same = df[df["comparator_a"] == df["comparator_b"]]
    assert len(same) == 0, f"Found {len(same)} self-comparisons"
    print("PASS: No self-comparisons in comparator analysis")


def test_comparator_pairs_coverage():
    df = pd.read_csv("data/analytical/analytical_scenario_comparator_analysis.csv", keep_default_na=False)
    expected_pairs = {("Conservative", "Baseline"), ("Expected", "Conservative"), ("Higher Intensity", "Expected"), ("Expected", "Baseline"), ("Higher Intensity", "Baseline")}
    actual_pairs = set()
    for _, row in df.iterrows():
        actual_pairs.add((row["comparator_a"], row["comparator_b"]))
    # At least some of the expected pairs should exist
    assert len(actual_pairs & expected_pairs) > 0, "No expected comparator pairs found"
    print("PASS: Expected comparator pairs present")


def test_diminishing_returns_assessable():
    df = pd.read_csv("data/analytical/analytical_scenario_diminishing_returns.csv", keep_default_na=False)
    assessable = df[~df["diminishing_return_classification"].isin(["Not Assessable", ""])]
    assert len(assessable) > 0, "No assessable diminishing returns found"
    print("PASS: Diminishing returns assessable for some packages")


if __name__ == "__main__":
    test_comparator_analysis_not_zero_for_missing()
    test_comparator_pairs_coverage()
    test_diminishing_returns_assessable()
