"""
Unit tests for the QueryParser module.

Tests cover Machine ID extraction (case-insensitive), Shift keyword
extraction, Date pattern extraction, combined filters, and edge cases.
"""

import unittest
from core.query_parser import QueryParser, QueryFilter


class TestQueryParser(unittest.TestCase):
    """Tests for QueryParser free-text query parsing."""

    def setUp(self) -> None:
        """Set up parser with sample known machines."""
        self.known_machines = [
            "Press_Line_1",
            "Press_Line_5",
            "CNC_Milling_3",
            "Assembly_Robot_2",
            "Injection_Mold_4",
        ]
        self.parser = QueryParser(known_machines=self.known_machines)

    # ------------------------------------------------------------------
    # Machine ID extraction
    # ------------------------------------------------------------------

    def test_extract_machine_id(self) -> None:
        """Should extract a known Machine ID from the query."""
        result = self.parser.parse("Show Press_Line_5")
        self.assertIsNotNone(result)
        self.assertEqual(result.machine_id, "Press_Line_5")

    def test_extract_machine_id_case_insensitive(self) -> None:
        """Machine ID matching should be case-insensitive."""
        result = self.parser.parse("show press_line_5")
        self.assertIsNotNone(result)
        self.assertEqual(result.machine_id, "Press_Line_5")

    def test_extract_machine_id_longest_match(self) -> None:
        """Should match the longest machine ID to avoid partial matches."""
        # Both "Press_Line_1" and "Press_Line_5" contain "Press_Line"
        # but the exact match should win
        result = self.parser.parse("Show Press_Line_1")
        self.assertIsNotNone(result)
        self.assertEqual(result.machine_id, "Press_Line_1")

    def test_unknown_machine_returns_none(self) -> None:
        """Unknown machine names should result in no filter."""
        result = self.parser.parse("Show Unknown_Machine_99")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # Shift extraction
    # ------------------------------------------------------------------

    def test_extract_morning_shift(self) -> None:
        """Should extract Morning shift keyword."""
        result = self.parser.parse("Show Press_Line_5 Morning Shift")
        self.assertIsNotNone(result)
        self.assertEqual(result.shift, "Morning")

    def test_extract_night_shift(self) -> None:
        """Should extract Night shift keyword."""
        result = self.parser.parse("Show CNC_Milling_3 Night Shift")
        self.assertIsNotNone(result)
        self.assertEqual(result.shift, "Night")

    def test_extract_afternoon_shift(self) -> None:
        """Should extract Afternoon shift keyword."""
        result = self.parser.parse("Show Press_Line_1 Afternoon")
        self.assertIsNotNone(result)
        self.assertEqual(result.shift, "Afternoon")

    def test_shift_case_insensitive(self) -> None:
        """Shift matching should be case-insensitive."""
        result = self.parser.parse("Show Press_Line_5 MORNING shift")
        self.assertIsNotNone(result)
        self.assertEqual(result.shift, "Morning")

    # ------------------------------------------------------------------
    # Date extraction
    # ------------------------------------------------------------------

    def test_extract_date(self) -> None:
        """Should extract ISO date from the query."""
        result = self.parser.parse("Show Press_Line_5 on 2026-06-18")
        self.assertIsNotNone(result)
        self.assertEqual(result.date, "2026-06-18")

    def test_date_without_preposition(self) -> None:
        """Should extract date even without 'on' keyword."""
        result = self.parser.parse("Show Press_Line_5 2026-06-18")
        self.assertIsNotNone(result)
        self.assertEqual(result.date, "2026-06-18")

    # ------------------------------------------------------------------
    # Combined filters
    # ------------------------------------------------------------------

    def test_machine_and_shift(self) -> None:
        """Should extract both Machine ID and Shift."""
        result = self.parser.parse("Show Press_Line_5 Morning Shift")
        self.assertIsNotNone(result)
        self.assertEqual(result.machine_id, "Press_Line_5")
        self.assertEqual(result.shift, "Morning")
        self.assertIsNone(result.date)

    def test_machine_and_date(self) -> None:
        """Should extract both Machine ID and Date."""
        result = self.parser.parse("Show Press_Line_5 on 2026-06-18")
        self.assertIsNotNone(result)
        self.assertEqual(result.machine_id, "Press_Line_5")
        self.assertEqual(result.date, "2026-06-18")
        self.assertIsNone(result.shift)

    def test_machine_shift_and_date(self) -> None:
        """Should extract all three filters."""
        result = self.parser.parse(
            "Show Press_Line_5 Morning Shift on 2026-06-18"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.machine_id, "Press_Line_5")
        self.assertEqual(result.shift, "Morning")
        self.assertEqual(result.date, "2026-06-18")

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_empty_query_returns_none(self) -> None:
        """Empty query should return None."""
        self.assertIsNone(self.parser.parse(""))

    def test_whitespace_only_returns_none(self) -> None:
        """Whitespace-only query should return None."""
        self.assertIsNone(self.parser.parse("   "))

    def test_no_filters_returns_none(self) -> None:
        """Query with no recognizable filters should return None."""
        self.assertIsNone(self.parser.parse("Hello world"))

    # ------------------------------------------------------------------
    # QueryFilter dataclass
    # ------------------------------------------------------------------

    def test_query_filter_is_empty(self) -> None:
        """Empty QueryFilter should report is_empty = True."""
        qf = QueryFilter()
        self.assertTrue(qf.is_empty)

    def test_query_filter_not_empty(self) -> None:
        """QueryFilter with any field set should report is_empty = False."""
        qf = QueryFilter(machine_id="Press_Line_5")
        self.assertFalse(qf.is_empty)

    def test_query_filter_describe(self) -> None:
        """describe() should return human-readable filter summary."""
        qf = QueryFilter(machine_id="Press_Line_5", shift="Morning")
        desc = qf.describe()
        self.assertIn("Press_Line_5", desc)
        self.assertIn("Morning", desc)


if __name__ == "__main__":
    unittest.main()
