import unittest
from llm.groq_client import GroqClient


class TestGroqClient(unittest.TestCase):

    def test_generate_fallback_response(self):
        client = GroqClient()
        records = [{"id": "1", "error_code": "DT-01"}]
        fallback = client._generate_fallback_response(records)

        self.assertEqual(len(fallback), 1)
        self.assertEqual(fallback[0]["predicted_pillar"], "Unknown")
        self.assertEqual(fallback[0]["root_cause"], "Unknown")
        self.assertEqual(fallback[0]["manager_summary"], "LLM unavailable")
        self.assertEqual(fallback[0]["classification_status"], "Pending Review")
        # Confidence must NOT exist
        self.assertNotIn("confidence", fallback[0])

    def test_fallback_preserves_ids(self):
        client = GroqClient()
        records = [
            {"id": "10", "error_code": "DT-01"},
            {"id": "20", "error_code": "DT-04"},
        ]
        fallback = client._generate_fallback_response(records)

        self.assertEqual(fallback[0]["id"], "10")
        self.assertEqual(fallback[1]["id"], "20")


if __name__ == "__main__":
    unittest.main()
