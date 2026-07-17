"""
Unit tests for the BusinessImpactEngine module.

Tests cover business loss calculation, production loss estimation,
downtime and scrap cost calculations, and priority scoring logic.
"""

import unittest
import pandas as pd
from analysis.business_impact import BusinessImpactEngine


class TestBusinessImpactEngine(unittest.TestCase):
    """Tests for the Business Impact calculations."""

    def setUp(self) -> None:
        """Initialize the engine with predictable config overrides."""
        self.engine = BusinessImpactEngine()
        # Override with predictable numbers for testing
        self.engine.downtime_cost_per_minute = 100.0
        self.engine.scrap_cost_per_part = 50.0
        self.engine.production_value_per_part = 200.0

    def _make_df(
        self,
        planned_time: float = 480.0,
        downtime: float = 0.0,
        ideal_cycle: float = 1.0,
        total_parts: int = 480,
        defects: int = 0,
        oee: float = 100.0,
        error_code: str = "DT-00",
    ) -> pd.DataFrame:
        """Helper to build a DataFrame mimicking OEECalculator output."""
        return pd.DataFrame(
            {
                "Machine ID": ["Test_Machine_1"],
                "Date": ["2026-06-18"],
                "Shift": ["Morning"],
                "Planned Time (min)": [planned_time],
                "Downtime (min)": [downtime],
                "Ideal Cycle Time (min/unit)": [ideal_cycle],
                "Total Parts Produced": [total_parts],
                "Defective Parts": [defects],
                "OEE": [oee],
                "Error Code": [error_code],
            }
        )

    def test_perfect_production(self) -> None:
        """Perfect production should result in zero loss."""
        df = self._make_df()
        result = self.engine.calculate(df)

        self.assertEqual(result.loc[0, "Production Loss (units)"], 0)
        self.assertEqual(result.loc[0, "Throughput Loss (units)"], 0)
        self.assertEqual(result.loc[0, "Downtime Cost"], 0.0)
        self.assertEqual(result.loc[0, "Scrap Cost"], 0.0)
        self.assertEqual(result.loc[0, "Estimated Business Loss"], 0.0)
        self.assertEqual(result.loc[0, "Priority"], "Low")
        self.assertEqual(result.loc[0, "Top Loss Driver Rank"], 1)

    def test_downtime_only(self) -> None:
        """Test calculation with only downtime (Availability Loss)."""
        # 480 min planned, 60 min down = 420 min operating
        # Ideal Cycle = 1.0. Expected parts = 480. Produced = 420.
        df = self._make_df(downtime=60.0, total_parts=420, oee=87.5, error_code="DT-01")
        result = self.engine.calculate(df)

        self.assertEqual(result.loc[0, "Production Loss (units)"], 60)
        self.assertEqual(result.loc[0, "Throughput Loss (units)"], 0)  # 420 / 1.0 - 420 = 0
        
        expected_downtime_cost = 60.0 * 100.0  # 6000
        expected_production_cost = 60 * 200.0  # 12000
        
        self.assertEqual(result.loc[0, "Downtime Cost"], expected_downtime_cost)
        self.assertEqual(result.loc[0, "Scrap Cost"], 0.0)
        self.assertEqual(
            result.loc[0, "Estimated Business Loss"],
            expected_downtime_cost + expected_production_cost
        )

    def test_throughput_loss_only(self) -> None:
        """Test calculation with speed reduction (Performance Loss)."""
        # 480 min operating, no downtime. Ideal Cycle = 1.0.
        # Total parts = 400 (missed 80 due to speed)
        df = self._make_df(total_parts=400, oee=83.33, error_code="DT-04")
        result = self.engine.calculate(df)

        self.assertEqual(result.loc[0, "Production Loss (units)"], 80)
        self.assertEqual(result.loc[0, "Throughput Loss (units)"], 80)
        self.assertEqual(result.loc[0, "Downtime Cost"], 0.0)
        self.assertEqual(result.loc[0, "Scrap Cost"], 0.0)
        self.assertEqual(result.loc[0, "Estimated Business Loss"], 80 * 200.0)

    def test_scrap_only(self) -> None:
        """Test calculation with only defective parts (Quality Loss)."""
        # 480 min, produced 480 parts, 50 defective.
        # Production Loss = Expected (480) - Total (480) = 0
        # Wait, scrap cost applies.
        df = self._make_df(total_parts=480, defects=50, oee=89.58, error_code="DT-07")
        result = self.engine.calculate(df)

        self.assertEqual(result.loc[0, "Production Loss (units)"], 0)
        self.assertEqual(result.loc[0, "Downtime Cost"], 0.0)
        self.assertEqual(result.loc[0, "Scrap Cost"], 50 * 50.0)
        self.assertEqual(result.loc[0, "Estimated Business Loss"], 2500.0)

    def test_combined_losses_and_priority_score(self) -> None:
        """Test multiple machines to verify relative Priority Score and Rank."""
        df = pd.DataFrame(
            {
                "Machine ID": ["M1", "M2", "M3"],
                "Planned Time (min)": [480, 480, 480],
                "Downtime (min)": [120, 60, 0],
                "Ideal Cycle Time (min/unit)": [1.0, 1.0, 1.0],
                "Total Parts Produced": [300, 400, 480],
                "Defective Parts": [20, 0, 0],
                "OEE": [58.33, 83.33, 100.0],
                "Error Code": ["DT-01", "DT-04", "DT-00"],
            }
        )
        
        result = self.engine.calculate(df)
        
        # M1 has 120m downtime, 180 production loss (480 - 300), 20 scrap
        # Loss M1 = (120*100) + (180*200) + (20*50) = 12000 + 36000 + 1000 = 49000
        self.assertEqual(result.loc[0, "Estimated Business Loss"], 49000.0)
        
        # M2 has 60m downtime, 80 production loss (480 - 400), 0 scrap
        # Loss M2 = (60*100) + (80*200) + 0 = 6000 + 16000 = 22000
        self.assertEqual(result.loc[1, "Estimated Business Loss"], 22000.0)
        
        # M3 has 0 loss
        self.assertEqual(result.loc[2, "Estimated Business Loss"], 0.0)
        
        # Verify Rank (Dense Rank Descending)
        # 49000 -> 1, 22000 -> 2, 0 -> 3
        # Since the function sorts by Top Loss Driver Rank, row 0 is M1
        self.assertEqual(result.loc[0, "Machine ID"], "M1")
        self.assertEqual(result.loc[0, "Top Loss Driver Rank"], 1)
        self.assertEqual(result.loc[1, "Machine ID"], "M2")
        self.assertEqual(result.loc[1, "Top Loss Driver Rank"], 2)
        self.assertEqual(result.loc[2, "Machine ID"], "M3")
        self.assertEqual(result.loc[2, "Top Loss Driver Rank"], 3)
        
        # Priority Score checks
        # M1: Max loss = 49000, Max downtime = 120. OEE = 58.33. Severity (DT-01) = 10.
        # Score = OEE(12.5) + Loss(40) + Downtime(20) + Severity(10) = ~82.5 (Critical)
        self.assertGreaterEqual(result.loc[0, "Priority Score"], 80)
        self.assertEqual(result.loc[0, "Priority"], "Critical")

    def test_empty_dataframe(self) -> None:
        """Empty DataFrame should be returned unchanged."""
        df = pd.DataFrame()
        result = self.engine.calculate(df)
        self.assertTrue(result.empty)


if __name__ == "__main__":
    unittest.main()
