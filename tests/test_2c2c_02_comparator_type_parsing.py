"""Test 2C-2C-02: Comparator type normalisation.

Verifies that parse_comparator_type handles all spelling variations
and never returns an unexpected value.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scenario_models import ComparatorType, parse_comparator_type


def test_parse_comparator_type():
    cases = [
        ("Baseline", ComparatorType.BASELINE),
        ("Conservative", ComparatorType.CONSERVATIVE),
        ("Expected", ComparatorType.EXPECTED),
        ("Higher Intensity", ComparatorType.HIGHER_INTENSITY),
        ("Higher-Intensity", ComparatorType.HIGHER_INTENSITY),
        ("higher intensity", ComparatorType.HIGHER_INTENSITY),
        ("Unknown", ComparatorType.BASELINE),
        ("", ComparatorType.BASELINE),
    ]
    for raw, expected in cases:
        result = parse_comparator_type(raw)
        assert result == expected, f"parse_comparator_type({raw!r}) = {result}, expected {expected}"
    print("PASS: All comparator type variations parse correctly")


if __name__ == "__main__":
    test_parse_comparator_type()
