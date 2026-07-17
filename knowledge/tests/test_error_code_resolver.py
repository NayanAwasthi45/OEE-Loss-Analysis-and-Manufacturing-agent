import unittest
import pandas as pd
from analysis.error_code_resolver import ErrorCodeResolver


class TestErrorCodeResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = ErrorCodeResolver()

    def test_resolve_known_code(self):
        df = pd.DataFrame({"Error Code": ["DT-01"]})
        result = self.resolver.resolve(df)

        self.assertEqual(result.loc[0, "Description"], "Mechanical Breakdown")
        self.assertEqual(result.loc[0, "OEE Impact"], "Availability")

    def test_resolve_dt00(self):
        df = pd.DataFrame({"Error Code": ["DT-00"]})
        result = self.resolver.resolve(df)

        self.assertEqual(result.loc[0, "Description"], "No Fault / Normal Operation")
        self.assertEqual(result.loc[0, "OEE Impact"], "None")

    def test_resolve_unknown_code_raises(self):
        df = pd.DataFrame({"Error Code": ["DT-99"]})
        with self.assertRaisesRegex(ValueError, "Unknown Error Code"):
            self.resolver.resolve(df)

    def test_resolve_all_known_codes(self):
        codes = [f"DT-0{i}" for i in range(9)]
        df = pd.DataFrame({"Error Code": codes})
        result = self.resolver.resolve(df)
        self.assertEqual(len(result), 9)
        self.assertIn("Description", result.columns)
        self.assertIn("Business Meaning", result.columns)
        self.assertIn("OEE Impact", result.columns)
        self.assertIn("Typical Downtime", result.columns)

    def test_valid_codes_property(self):
        codes = self.resolver.valid_codes
        self.assertIn("DT-00", codes)
        self.assertIn("DT-08", codes)
        self.assertEqual(len(codes), 9)


if __name__ == "__main__":
    unittest.main()
