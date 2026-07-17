"""
Unit tests for the OEECalculator module.

Tests cover normal OEE calculation, divide-by-zero edge cases,
loss column calculations, dominant loss classification with
Mixed Loss and No Significant Loss thresholds.
"""

import unittest
import pandas as pd
from core.oee_calculator import OEECalculator


class TestOEECalculator(unittest.TestCase):
    """Tests for OEECalculator deterministic calculations."""

    def setUp(self) -> None:
        self.calculator = OEECalculator()

    # ------------------------------------------------------------------
    # Core OEE calculations
    # ------------------------------------------------------------------

    def test_normal_calculation(self) -> None:
        """Standard OEE calculation with typical production values."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [90],
                "Total Parts Produced": [320],
                "Defective Parts": [5],
                "Ideal Cycle Time (min/unit)": [1.0],
            }
        )

        result = self.calculator.calculate(df)

        # Operating Time = 390
        # Availability = 390/480 = 81.25%
        # Performance = (320*1.0)/390 ≈ 82.05%
        # Quality = 315/320 ≈ 98.44%
        self.assertAlmostEqual(result.loc[0, "Availability"], 81.25)
        self.assertAlmostEqual(result.loc[0, "Performance"], 82.05)
        self.assertAlmostEqual(result.loc[0, "Quality"], 98.44)
        self.assertAlmostEqual(result.loc[0, "OEE"], 65.62)

    def test_divide_by_zero_planned_time(self) -> None:
        """Zero planned time should produce zero OEE metrics."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [0],
                "Downtime (min)": [0],
                "Total Parts Produced": [0],
                "Defective Parts": [0],
                "Ideal Cycle Time (min/unit)": [1.0],
            }
        )
        result = self.calculator.calculate(df)
        self.assertEqual(result.loc[0, "Availability"], 0.0)
        self.assertEqual(result.loc[0, "OEE"], 0.0)

    def test_divide_by_zero_operating_time(self) -> None:
        """Full downtime should produce zero performance and OEE."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [480],
                "Total Parts Produced": [0],
                "Defective Parts": [0],
                "Ideal Cycle Time (min/unit)": [1.0],
            }
        )
        result = self.calculator.calculate(df)
        self.assertEqual(result.loc[0, "Availability"], 0.0)
        self.assertEqual(result.loc[0, "Performance"], 0.0)
        self.assertEqual(result.loc[0, "OEE"], 0.0)

    def test_divide_by_zero_total_parts(self) -> None:
        """Zero parts produced should produce zero quality and performance."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [0],
                "Total Parts Produced": [0],
                "Defective Parts": [0],
                "Ideal Cycle Time (min/unit)": [1.0],
            }
        )
        result = self.calculator.calculate(df)
        self.assertEqual(result.loc[0, "Quality"], 0.0)
        self.assertEqual(result.loc[0, "Performance"], 0.0)
        self.assertEqual(result.loc[0, "OEE"], 0.0)

    # ------------------------------------------------------------------
    # Loss columns
    # ------------------------------------------------------------------

    def test_loss_columns_calculated(self) -> None:
        """Availability/Performance/Quality Loss should be 100 - metric."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [90],
                "Total Parts Produced": [320],
                "Defective Parts": [5],
                "Ideal Cycle Time (min/unit)": [1.0],
            }
        )
        result = self.calculator.calculate(df)

        self.assertAlmostEqual(result.loc[0, "Availability Loss"], 18.75)
        self.assertAlmostEqual(result.loc[0, "Performance Loss"], 17.95)
        self.assertAlmostEqual(result.loc[0, "Quality Loss"], 1.56)

    def test_loss_columns_exist(self) -> None:
        """All loss columns and Dominant Loss should be present."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [90],
                "Total Parts Produced": [320],
                "Defective Parts": [5],
                "Ideal Cycle Time (min/unit)": [1.0],
            }
        )
        result = self.calculator.calculate(df)

        self.assertIn("Availability Loss", result.columns)
        self.assertIn("Performance Loss", result.columns)
        self.assertIn("Quality Loss", result.columns)
        self.assertIn("Dominant Loss", result.columns)

    # ------------------------------------------------------------------
    # Dominant loss classification
    # ------------------------------------------------------------------

    def test_clear_dominant_loss(self) -> None:
        """When one loss is clearly dominant (> 5% gap), return its name."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [144],  # Avail = 70%, Loss = 30%
                "Total Parts Produced": [300],
                "Defective Parts": [5],  # Quality ≈ 98.3%, Loss ≈ 1.7%
                "Ideal Cycle Time (min/unit)": [1.0],  # Perf = 300/336 ≈ 89.3%, Loss ≈ 10.7%
            }
        )
        result = self.calculator.calculate(df)
        self.assertEqual(result.loc[0, "Dominant Loss"], "Availability")

    def test_mixed_loss(self) -> None:
        """When top two losses differ by < 5%, return Mixed Loss string."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [90],  # Avail = 81.25%, Loss = 18.75%
                "Total Parts Produced": [320],
                "Defective Parts": [5],
                "Ideal Cycle Time (min/unit)": [1.0],  # Perf ≈ 82.05%, Loss ≈ 17.95%
            }
        )
        result = self.calculator.calculate(df)
        dominant = result.loc[0, "Dominant Loss"]
        self.assertTrue(dominant.startswith("Mixed Loss"))
        self.assertIn("Availability", dominant)
        self.assertIn("Performance", dominant)

    def test_no_significant_loss(self) -> None:
        """When highest loss < 8%, return 'No Significant Loss'."""
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [10],  # Avail ≈ 97.9%, Loss ≈ 2.1%
                "Total Parts Produced": [450],
                "Defective Parts": [2],  # Quality ≈ 99.6%, Loss ≈ 0.4%
                "Ideal Cycle Time (min/unit)": [1.0],  # Perf ≈ 95.7%, Loss ≈ 4.3%
            }
        )
        result = self.calculator.calculate(df)
        self.assertEqual(result.loc[0, "Dominant Loss"], "No Significant Loss")

    def test_no_significant_loss_prevents_mixed_loss(self) -> None:
        """
        No Significant Loss threshold should take priority over
        Mixed Loss when all losses are small (e.g., DT-00 records).
        """
        df = pd.DataFrame(
            {
                "Planned Time (min)": [480],
                "Downtime (min)": [5],  # Avail ≈ 98.96%, Loss ≈ 1.04%
                "Total Parts Produced": [470],
                "Defective Parts": [3],  # Quality ≈ 99.36%, Loss ≈ 0.64%
                "Ideal Cycle Time (min/unit)": [1.0],  # Perf ≈ 98.95%, Loss ≈ 1.05%
            }
        )
        result = self.calculator.calculate(df)
        # All three losses < 8% → No Significant Loss
        # (Not Mixed Loss even though they're within 5% of each other)
        self.assertEqual(result.loc[0, "Dominant Loss"], "No Significant Loss")


if __name__ == "__main__":
    unittest.main()
