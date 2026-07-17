"""
Unit tests for the ErrorCodeResolver module.

Tests cover known code resolution (Description + Typical Downtime only),
unknown code errors, all known codes, and the valid_codes property.
Business Meaning and OEE Impact are intentionally NOT tested as they
are internal knowledge and no longer exposed in resolver output.
"""

import unittest
import pandas as pd
from analysis.error_code_resolver import ErrorCodeResolver


class TestErrorCodeResolver(unittest.TestCase):
    """Tests for ErrorCodeResolver deterministic lookup."""

    def setUp(self) -> None:
        self.resolver = ErrorCodeResolver()

    def test_resolve_known_code(self) -> None:
        """Known error code should resolve to Description and Typical Downtime."""
        df = pd.DataFrame({"Error Code": ["DT-01"]})
        result = self.resolver.resolve(df)

        self.assertEqual(result.loc[0, "Description"], "Mechanical Breakdown")
        self.assertEqual(result.loc[0, "Typical Downtime"], "30-240")

    def test_resolve_dt00(self) -> None:
        """DT-00 should resolve to No Fault / Normal Operation."""
        df = pd.DataFrame({"Error Code": ["DT-00"]})
        result = self.resolver.resolve(df)

        self.assertEqual(result.loc[0, "Description"], "No Fault / Normal Operation")
        self.assertEqual(result.loc[0, "Typical Downtime"], "0")

    def test_resolve_unknown_code_raises(self) -> None:
        """Unknown error code should raise ValueError."""
        df = pd.DataFrame({"Error Code": ["DT-99"]})
        with self.assertRaisesRegex(ValueError, "Unknown Error Code"):
            self.resolver.resolve(df)

    def test_resolve_all_known_codes(self) -> None:
        """All 9 known codes should resolve with Description and Typical Downtime."""
        codes = [f"DT-0{i}" for i in range(9)]
        df = pd.DataFrame({"Error Code": codes})
        result = self.resolver.resolve(df)

        self.assertEqual(len(result), 9)
        self.assertIn("Description", result.columns)
        self.assertIn("Typical Downtime", result.columns)

    def test_business_meaning_not_exposed(self) -> None:
        """Business Meaning should NOT be in the resolver output."""
        df = pd.DataFrame({"Error Code": ["DT-01"]})
        result = self.resolver.resolve(df)
        self.assertNotIn("Business Meaning", result.columns)

    def test_oee_impact_not_exposed(self) -> None:
        """OEE Impact should NOT be in the resolver output."""
        df = pd.DataFrame({"Error Code": ["DT-01"]})
        result = self.resolver.resolve(df)
        self.assertNotIn("OEE Impact", result.columns)

    def test_valid_codes_property(self) -> None:
        """valid_codes should return the set of all known error codes."""
        codes = self.resolver.valid_codes
        self.assertIn("DT-00", codes)
        self.assertIn("DT-08", codes)
        self.assertEqual(len(codes), 9)


if __name__ == "__main__":
    unittest.main()
