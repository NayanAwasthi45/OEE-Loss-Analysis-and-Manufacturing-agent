"""
Unit tests for the GroqClient module.

Tests cover fallback response generation with the current output schema
(ai_validation, validation_reason, likely_root_cause, manufacturing_insight),
rate-limit response generation, and ID preservation.
"""

import unittest
from llm.groq_client import GroqClient


class TestGroqClient(unittest.TestCase):
    """Tests for GroqClient fallback and rate-limit responses."""

    def test_generate_fallback_response(self) -> None:
        """Fallback should use Skipped with Not Applicable root cause."""
        client = GroqClient()
        records = [{"id": "1", "error_code": "DT-01"}]
        fallback = client._generate_fallback_response(records)

        self.assertEqual(len(fallback), 1)
        self.assertEqual(fallback[0]["ai_validation"], "Skipped")
        self.assertEqual(fallback[0]["validation_reason"], "LLM Unavailable. Manual review required.")
        self.assertEqual(fallback[0]["likely_root_cause"], "Not Applicable")
        self.assertIn("unavailable", fallback[0]["manufacturing_insight"].lower())

        # Old column names must NOT exist
        self.assertNotIn("predicted_pillar", fallback[0])
        self.assertNotIn("manager_summary", fallback[0])
        self.assertNotIn("classification_status", fallback[0])
        self.assertNotIn("confidence", fallback[0])

    def test_fallback_preserves_ids(self) -> None:
        """Fallback responses should preserve original record IDs."""
        client = GroqClient()
        records = [
            {"id": "10", "error_code": "DT-01"},
            {"id": "20", "error_code": "DT-04"},
        ]
        fallback = client._generate_fallback_response(records)

        self.assertEqual(fallback[0]["id"], "10")
        self.assertEqual(fallback[1]["id"], "20")

    def test_rate_limit_response(self) -> None:
        """Rate limit response should use Skipped with Not Applicable root cause."""
        client = GroqClient()
        records = [{"id": "5", "error_code": "DT-02"}]
        rate_limited = client._generate_rate_limit_response(records)

        self.assertEqual(len(rate_limited), 1)
        self.assertEqual(rate_limited[0]["ai_validation"], "Skipped")
        self.assertEqual(rate_limited[0]["validation_reason"], "Rate Limit. Record skipped.")
        self.assertEqual(rate_limited[0]["likely_root_cause"], "Not Applicable")
        self.assertIn("rate limit", rate_limited[0]["manufacturing_insight"].lower())

    def test_rate_limit_preserves_ids(self) -> None:
        """Rate limit responses should preserve original record IDs."""
        client = GroqClient()
        records = [
            {"id": "100", "error_code": "DT-03"},
            {"id": "200", "error_code": "DT-06"},
        ]
        rate_limited = client._generate_rate_limit_response(records)

        self.assertEqual(rate_limited[0]["id"], "100")
        self.assertEqual(rate_limited[1]["id"], "200")

    def test_no_unknown_or_pending_review(self) -> None:
        """Neither fallback nor rate-limit should use Unknown/Pending Review."""
        client = GroqClient()
        records = [{"id": "1", "error_code": "DT-01"}]

        for response_list in [
            client._generate_fallback_response(records),
            client._generate_rate_limit_response(records),
        ]:
            for response in response_list:
                self.assertNotEqual(response.get("ai_validation"), "Unknown")
                self.assertNotEqual(response.get("ai_validation"), "Pending Review")
                self.assertNotEqual(response.get("likely_root_cause"), "Unknown")

    def test_no_none_root_cause(self) -> None:
        """Root cause should never be 'None' — should be 'Not Applicable'."""
        client = GroqClient()
        records = [{"id": "1", "error_code": "DT-01"}]

        for response_list in [
            client._generate_fallback_response(records),
            client._generate_rate_limit_response(records),
        ]:
            for response in response_list:
                self.assertNotEqual(response.get("likely_root_cause"), "None")
                self.assertEqual(response.get("likely_root_cause"), "Not Applicable")


if __name__ == "__main__":
    unittest.main()
