"""
Unit tests for the LossAnalyzer (Manufacturing Intelligence) module.

Tests cover AI pre-filtering, output columns (AI Validation, Validation Reason,
Likely Root Cause, Manufacturing Insight), healthy record skipping,
No Significant Loss handling, rate-limit responses, and LLM fallback.
"""

import unittest
import pandas as pd
from analysis.loss_analyzer import LossAnalyzer


class TestLossAnalyzer(unittest.TestCase):
    """Tests for LossAnalyzer AI orchestration."""

    def _make_df(
        self,
        availability: float,
        performance: float,
        quality: float,
        error_code: str = "DT-01",
    ) -> pd.DataFrame:
        """
        Helper to build a minimal enriched DataFrame for testing.

        Includes all columns that would be present after OEECalculator
        and ErrorCodeResolver have run.
        """
        avail_loss = round(100.0 - availability, 2)
        perf_loss = round(100.0 - performance, 2)
        qual_loss = round(100.0 - quality, 2)
        oee = round(availability * performance * quality / 10000, 2)

        # Determine dominant loss
        losses = {
            "Availability": avail_loss,
            "Performance": perf_loss,
            "Quality": qual_loss,
        }
        sorted_losses = sorted(losses.items(), key=lambda x: x[1], reverse=True)
        first_name, first_val = sorted_losses[0]
        second_name, second_val = sorted_losses[1]

        if first_val < 8.0:
            dominant = "No Significant Loss"
        elif (first_val - second_val) < 5.0:
            dominant = (
                f"Mixed Loss - {first_name} ({first_val:.2f}%) "
                f"+ {second_name} ({second_val:.2f}%)"
            )
        else:
            dominant = first_name

        return pd.DataFrame(
            {
                "Machine ID": ["Press_Line_1"],
                "Shift": ["Morning"],
                "Error Code": [error_code],
                "Description": ["Mechanical Breakdown"],
                "Typical Downtime": ["30-240"],
                "Availability": [availability],
                "Performance": [performance],
                "Quality": [quality],
                "OEE": [oee],
                "Availability Loss": [avail_loss],
                "Performance Loss": [perf_loss],
                "Quality Loss": [qual_loss],
                "Dominant Loss": [dominant],
            }
        )

    # ------------------------------------------------------------------
    # AI output columns
    # ------------------------------------------------------------------

    def test_ai_verified_output(self) -> None:
        """AI should return Verified validation with specific root cause."""
        df = self._make_df(70.0, 90.0, 95.0)

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {
                "id": "0",
                "ai_validation": "Verified",
                "validation_reason": "Availability loss of 30% aligns with expected high Availability impact from DT-01. The [Needs Attention] classification is consistent with recurring unplanned downtime.",
                "likely_root_cause": "Hydraulic seal wear due to fluid contamination",
                "manufacturing_insight": "The 30% availability loss on this Press Line matches the DT-01 breakdown pattern. Availability falls in the [Needs Attention] band, consistent with TPM Breakdown Losses from mechanical component failure.",
            }
        ]

        result = analyzer.analyze(df)
        self.assertEqual(result.loc[0, "AI Validation"], "Verified")
        self.assertIn("Needs Attention", result.loc[0, "Validation Reason"])
        self.assertEqual(result.loc[0, "Likely Root Cause"], "Hydraulic seal wear due to fluid contamination")
        self.assertIn("Press Line", result.loc[0, "Manufacturing Insight"])

    def test_ai_mismatch_output(self) -> None:
        """AI should return Mismatch when error code contradicts losses."""
        df = self._make_df(70.0, 90.0, 95.0)

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {
                "id": "0",
                "ai_validation": "Mismatch",
                "validation_reason": "DT-04 expects Performance loss from small stops, but the dominant loss is Availability at 30%. This contradicts the playbook's expected low Availability impact.",
                "likely_root_cause": "Sensor drift on temperature probe",
                "manufacturing_insight": "Dominant Availability loss contradicts the DT-04 small-stop pattern expected for this Assembly Line. The [Needs Attention] Availability classification suggests unplanned downtime rather than micro-stoppages.",
            }
        ]

        result = analyzer.analyze(df)
        self.assertEqual(result.loc[0, "AI Validation"], "Mismatch")
        self.assertNotEqual(result.loc[0, "Likely Root Cause"], "Unknown")
        self.assertNotEqual(result.loc[0, "Likely Root Cause"], "Mechanical Breakdown")

    # ------------------------------------------------------------------
    # Healthy record skipping
    # ------------------------------------------------------------------

    def test_healthy_record_skipped(self) -> None:
        """
        DT-00 records with high OEE and low losses should be skipped.
        AI Validation = 'Skipped', Likely Root Cause = 'Not Applicable'.
        """
        df = self._make_df(99.0, 98.0, 99.5, error_code="DT-00")

        analyzer = LossAnalyzer()
        # LLM should NOT be called — mock to fail if invoked
        analyzer.llm_client.batch_analyze = lambda recs: (
            self.fail("LLM should not be called for healthy records")
        )

        result = analyzer.analyze(df)
        self.assertEqual(result.loc[0, "AI Validation"], "Skipped")
        self.assertEqual(
            result.loc[0, "Validation Reason"],
            "Healthy production record. No manufacturing anomalies requiring AI analysis.",
        )
        self.assertEqual(result.loc[0, "Likely Root Cause"], "Not Applicable")
        self.assertEqual(
            result.loc[0, "Manufacturing Insight"],
            "Production metrics remain within expected operating thresholds. No abnormal manufacturing behaviour was detected.",
        )
        self.assertEqual(analyzer.ai_skipped_count, 1)
        self.assertEqual(analyzer.ai_processed_count, 0)

    def test_dt00_but_low_oee_still_analyzed(self) -> None:
        """
        Even DT-00 with abnormally low OEE should be sent to AI
        (since OEE < 85% triggers AI eligibility).
        """
        df = self._make_df(70.0, 80.0, 90.0, error_code="DT-00")

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {
                "id": "0",
                "ai_validation": "Mismatch",
                "validation_reason": "DT-00 logged but significant losses observed across all pillars.",
                "likely_root_cause": "Unreported conveyor belt misalignment",
                "manufacturing_insight": "DT-00 baseline state contradicts the observed 30% Availability loss. The [Needs Attention] classification suggests unlogged downtime events.",
            }
        ]

        result = analyzer.analyze(df)
        self.assertEqual(result.loc[0, "AI Validation"], "Mismatch")
        self.assertEqual(analyzer.ai_processed_count, 1)

    # ------------------------------------------------------------------
    # AI processing statistics
    # ------------------------------------------------------------------

    def test_ai_stats_tracked(self) -> None:
        """Analyzer should track processed and skipped counts."""
        df = self._make_df(70.0, 90.0, 95.0)

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {
                "id": "0",
                "ai_validation": "Verified",
                "validation_reason": "Loss pattern matches playbook expectations.",
                "likely_root_cause": "Bearing fatigue from inadequate lubrication",
                "manufacturing_insight": "Loss pattern consistent with TPM Breakdown Losses on Press Line equipment.",
            }
        ]

        analyzer.analyze(df)
        self.assertEqual(analyzer.ai_processed_count, 1)
        self.assertEqual(analyzer.ai_skipped_count, 0)

    # ------------------------------------------------------------------
    # Removed columns
    # ------------------------------------------------------------------

    def test_no_predicted_pillar_column(self) -> None:
        """Predicted Pillar column should NOT exist in output."""
        df = self._make_df(70.0, 90.0, 95.0)

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {
                "id": "0",
                "ai_validation": "Verified",
                "validation_reason": "Pattern matches expected behaviour.",
                "likely_root_cause": "Bearing fatigue from inadequate lubrication",
                "manufacturing_insight": "Consistent loss pattern.",
            }
        ]

        result = analyzer.analyze(df)
        self.assertNotIn("Predicted Pillar", result.columns)
        self.assertNotIn("Manager Summary", result.columns)
        self.assertNotIn("Classification Status", result.columns)
        self.assertNotIn("Confidence", result.columns)

    # ------------------------------------------------------------------
    # Fallback / LLM unavailable
    # ------------------------------------------------------------------

    def test_llm_fallback_uses_skipped(self) -> None:
        """When LLM is unavailable, should use Skipped with Not Applicable root cause."""
        df = self._make_df(70.0, 90.0, 95.0)

        analyzer = LossAnalyzer()
        analyzer.llm_client.batch_analyze = lambda recs: [
            {
                "id": "0",
                "ai_validation": "Skipped",
                "validation_reason": "LLM Unavailable. Manual review required.",
                "likely_root_cause": "Not Applicable",
                "manufacturing_insight": "LLM service unavailable. No manufacturing insight could be generated.",
            }
        ]

        result = analyzer.analyze(df)
        self.assertEqual(result.loc[0, "AI Validation"], "Skipped")
        self.assertEqual(result.loc[0, "Likely Root Cause"], "Not Applicable")
        self.assertNotEqual(result.loc[0, "AI Validation"], "Unknown")
        self.assertNotEqual(result.loc[0, "AI Validation"], "Pending Review")

    # ------------------------------------------------------------------
    # Empty dataframe
    # ------------------------------------------------------------------

    def test_empty_dataframe(self) -> None:
        """Empty DataFrame should be returned unchanged."""
        df = pd.DataFrame()
        analyzer = LossAnalyzer()
        result = analyzer.analyze(df)
        self.assertTrue(result.empty)


if __name__ == "__main__":
    unittest.main()
