import unittest
import pandas as pd
from core.validator import DataValidator


class TestDataValidator(unittest.TestCase):

    def setUp(self):
        self.validator = DataValidator()
        self.valid_data = pd.DataFrame({
            "Date": ["2026-07-13"],
            "Machine ID": ["Press_Line_1"],
            "Shift": ["Morning"],
            "Planned Time (min)": [480],
            "Downtime (min)": [90],
            "Total Parts Produced": [320],
            "Defective Parts": [5],
            "Ideal Cycle Time (min/unit)": [1.0],
            "Error Code": ["DT-01"],
            "Operator ID": ["OP-492"],
        })

    def test_valid_dataframe(self):
        result = self.validator.validate(self.valid_data)
        self.assertEqual(len(result), 1)

    def test_missing_columns(self):
        invalid = self.valid_data.drop(columns=["Shift"])
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            self.validator.validate(invalid)

    def test_planned_time_zero(self):
        invalid = self.valid_data.copy()
        invalid.loc[0, "Planned Time (min)"] = 0
        with self.assertRaisesRegex(ValueError, "'Planned Time \\(min\\)' must be > 0"):
            self.validator.validate(invalid)

    def test_downtime_negative(self):
        invalid = self.valid_data.copy()
        invalid.loc[0, "Downtime (min)"] = -10
        with self.assertRaisesRegex(ValueError, "'Downtime \\(min\\)' must be >= 0"):
            self.validator.validate(invalid)

    def test_downtime_greater_than_planned(self):
        invalid = self.valid_data.copy()
        invalid.loc[0, "Downtime (min)"] = 500
        with self.assertRaisesRegex(
            ValueError, "'Downtime \\(min\\)' cannot be greater"
        ):
            self.validator.validate(invalid)

    def test_defective_greater_than_total(self):
        invalid = self.valid_data.copy()
        invalid.loc[0, "Defective Parts"] = 350
        with self.assertRaisesRegex(
            ValueError, "'Total Parts Produced' must be >= 'Defective Parts'"
        ):
            self.validator.validate(invalid)

    def test_ideal_cycle_time_zero(self):
        invalid = self.valid_data.copy()
        invalid.loc[0, "Ideal Cycle Time (min/unit)"] = 0
        with self.assertRaisesRegex(
            ValueError, "'Ideal Cycle Time \\(min/unit\\)' must be > 0"
        ):
            self.validator.validate(invalid)

    def test_empty_dataframe(self):
        with self.assertRaisesRegex(ValueError, "DataFrame is empty"):
            self.validator.validate(pd.DataFrame())

    def test_unknown_error_code(self):
        invalid = self.valid_data.copy()
        invalid.loc[0, "Error Code"] = "DT-99"
        with self.assertRaisesRegex(ValueError, "Unknown Error Codes"):
            self.validator.validate(invalid)


if __name__ == "__main__":
    unittest.main()
