import unittest
import pandas as pd
from analysis.loss_analyzer import LossAnalyzer


class TestLossAnalyzer(unittest.TestCase):

    def _make_df(self, availability, performance, quality, error_code="DT-01"):
        """Helper to build a minimal enriched DataFrame for testing."""
        return pd.DataFrame({
            "Machine ID": ["Press_Line_1"],
            "Shift": ["Morning"],
            "Error Code": [error_code],
            "Description": ["Mechanical Breakdown"],
            "Business Meaning": ["Mechanical failure"],
            "Typical Downtime": ["30-240"],
            "Availability": [availability],
            "Performance": [performance],
            "Quality": [quality],
        })

    def test_mixed_loss_partially_consistent(self):
        """Top two losses differ by < 5 % → Mixed Loss. LLM picks one of them."""
        df = self._make_df(80.0, 81.0, 95.0)  # Losses: 20, 19, 5

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {"id": "0", "predicted_pillar": "Availability",
             "root_cause": "Belt wear", "manager_summary": "Belt issue."}
        ]

        result = analyzer.analyze(df)
        self.assertTrue(result.loc[0, "Dominant Loss"].startswith("Mixed Loss"))
        self.assertIn("Availability", result.loc[0, "Dominant Loss"])
        self.assertIn("Performance", result.loc[0, "Dominant Loss"])
        self.assertEqual(result.loc[0, "Classification Status"], "Partially Consistent")

    def test_mixed_loss_needs_review(self):
        """Mixed Loss but LLM picks a pillar NOT in the mixed pair."""
        df = self._make_df(80.0, 81.0, 95.0)

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {"id": "0", "predicted_pillar": "Quality",
             "root_cause": "Scrap", "manager_summary": "Scrap."}
        ]

        result = analyzer.analyze(df)
        self.assertTrue(result.loc[0, "Dominant Loss"].startswith("Mixed Loss"))
        self.assertEqual(result.loc[0, "Classification Status"], "Needs Review")

    def test_clear_dominant_consistent(self):
        """Clear dominant loss matches LLM prediction."""
        df = self._make_df(70.0, 90.0, 95.0)  # Losses: 30, 10, 5

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {"id": "0", "predicted_pillar": "Availability",
             "root_cause": "Shaft failure", "manager_summary": "Shaft broke."}
        ]

        result = analyzer.analyze(df)
        self.assertEqual(result.loc[0, "Dominant Loss"], "Availability")
        self.assertEqual(result.loc[0, "Classification Status"], "Consistent")

    def test_dt00_normal_operation(self):
        """DT-00 should be handled gracefully by consistency logic."""
        df = self._make_df(99.0, 98.0, 99.5, error_code="DT-00")

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {"id": "0", "predicted_pillar": "No Significant Loss",
             "root_cause": "None", "manager_summary": "Machine operated normally."}
        ]

        result = analyzer.analyze(df)
        self.assertEqual(result.loc[0, "Predicted Pillar"], "No Significant Loss")
        # With such small losses the dominant is Mixed Loss, so "No Significant Loss"
        # triggers the Consistent path.
        self.assertEqual(result.loc[0, "Classification Status"], "Consistent")

    def test_unknown_fallback(self):
        """LLM returns Unknown → Pending Review."""
        df = self._make_df(70.0, 90.0, 95.0)

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {"id": "0", "predicted_pillar": "Unknown",
             "root_cause": "Unknown", "manager_summary": "LLM unavailable"}
        ]

        result = analyzer.analyze(df)
        self.assertEqual(result.loc[0, "Classification Status"], "Pending Review")


if __name__ == "__main__":
    unittest.main()
