import unittest
import pandas as pd
from core.oee_calculator import OEECalculator


class TestOEECalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = OEECalculator()

    def test_normal_calculation(self):
        df = pd.DataFrame({
            "Planned Time (min)": [480],
            "Downtime (min)": [90],
            "Total Parts Produced": [320],
            "Defective Parts": [5],
            "Ideal Cycle Time (min/unit)": [1.0],
        })

        result = self.calculator.calculate(df)

        # Operating Time = 390
        # Availability = 390/480 = 81.25%
        # Performance = (320*1.0)/390 ≈ 82.05%
        # Quality = 315/320 ≈ 98.44%
        self.assertAlmostEqual(result.loc[0, "Availability"], 81.25)
        self.assertAlmostEqual(result.loc[0, "Performance"], 82.05)
        self.assertAlmostEqual(result.loc[0, "Quality"], 98.44)
        self.assertAlmostEqual(result.loc[0, "OEE"], 65.62)

    def test_divide_by_zero_planned_time(self):
        df = pd.DataFrame({
            "Planned Time (min)": [0],
            "Downtime (min)": [0],
            "Total Parts Produced": [0],
            "Defective Parts": [0],
            "Ideal Cycle Time (min/unit)": [1.0],
        })
        result = self.calculator.calculate(df)
        self.assertEqual(result.loc[0, "Availability"], 0.0)
        self.assertEqual(result.loc[0, "OEE"], 0.0)

    def test_divide_by_zero_operating_time(self):
        df = pd.DataFrame({
            "Planned Time (min)": [480],
            "Downtime (min)": [480],
            "Total Parts Produced": [0],
            "Defective Parts": [0],
            "Ideal Cycle Time (min/unit)": [1.0],
        })
        result = self.calculator.calculate(df)
        self.assertEqual(result.loc[0, "Availability"], 0.0)
        self.assertEqual(result.loc[0, "Performance"], 0.0)
        self.assertEqual(result.loc[0, "OEE"], 0.0)

    def test_divide_by_zero_total_parts(self):
        df = pd.DataFrame({
            "Planned Time (min)": [480],
            "Downtime (min)": [0],
            "Total Parts Produced": [0],
            "Defective Parts": [0],
            "Ideal Cycle Time (min/unit)": [1.0],
        })
        result = self.calculator.calculate(df)
        self.assertEqual(result.loc[0, "Quality"], 0.0)
        self.assertEqual(result.loc[0, "Performance"], 0.0)
        self.assertEqual(result.loc[0, "OEE"], 0.0)


if __name__ == "__main__":
    unittest.main()
