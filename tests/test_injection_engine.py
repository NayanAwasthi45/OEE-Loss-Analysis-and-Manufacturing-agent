"""
Unit tests for the KnowledgeInjectionEngine module.

Tests cover JSON loading, machine profile detection, playbook retrieval
with operational/mechanical causes, OEE threshold evaluation with
classification labels, Six Big Losses matching with definitions,
and comprehensive context building.
"""

import unittest
from knowledge.injection_engine import KnowledgeInjectionEngine


class TestKnowledgeInjectionEngine(unittest.TestCase):
    """Tests for the KnowledgeInjectionEngine."""

    def setUp(self) -> None:
        """Initialize the engine once for all tests."""
        self.engine = KnowledgeInjectionEngine()

    # ------------------------------------------------------------------
    # JSON loading
    # ------------------------------------------------------------------

    def test_json_files_loaded(self) -> None:
        """Engine should load all four JSON files successfully."""
        self.assertIn("machine_profiles", self.engine.machine_profiles)
        self.assertIn("error_codes", self.engine.playbook)
        self.assertIn("availability_thresholds", self.engine.oee_guidelines)
        self.assertIn("six_big_losses", self.engine.six_big_losses)

    # ------------------------------------------------------------------
    # Machine Profile
    # ------------------------------------------------------------------

    def test_machine_profile_detection_press_line(self) -> None:
        """Should detect Press Line family with purpose and failure modes."""
        profile = self.engine._get_machine_profile("Press_Line_5")
        self.assertIn("Press Line", profile)
        self.assertIn("Purpose:", profile)
        self.assertIn("Expected Operating Behaviour:", profile)
        self.assertIn("Common Failure Modes:", profile)
        self.assertIn("Degradation Indicators:", profile)

    def test_machine_profile_detection_cnc(self) -> None:
        """Should detect CNC Milling family."""
        profile = self.engine._get_machine_profile("CNC_Milling_3")
        self.assertIn("CNC Milling", profile)
        self.assertIn("spindle", profile.lower())

    def test_machine_profile_detection_assembly(self) -> None:
        """Should detect Assembly Line family."""
        profile = self.engine._get_machine_profile("Assembly_Robot_2")
        self.assertIn("Assembly Line", profile)

    def test_machine_profile_unknown(self) -> None:
        """Unknown machine should return generic fallback."""
        profile = self.engine._get_machine_profile("Unknown_Machine_99")
        self.assertIn("Unknown", profile)

    # ------------------------------------------------------------------
    # Playbook Entry
    # ------------------------------------------------------------------

    def test_playbook_entry_retrieval(self) -> None:
        """Should retrieve correct playbook entry for DT-01 with causes."""
        entry = self.engine._get_playbook_entry("DT-01")
        self.assertIn("DT-01", entry)
        self.assertIn("Breakdown", entry)
        self.assertIn("Expected OEE Behaviour:", entry)
        self.assertIn("Possible Mechanical Causes:", entry)
        self.assertIn("Possible Operational Causes:", entry)

    def test_playbook_entry_has_symptoms(self) -> None:
        """Playbook entry should include machine symptoms."""
        entry = self.engine._get_playbook_entry("DT-02")
        self.assertIn("Typical Symptoms:", entry)

    def test_playbook_entry_unknown(self) -> None:
        """Unknown error code should return fallback."""
        entry = self.engine._get_playbook_entry("DT-99")
        self.assertIn("No playbook entry found", entry)

    # ------------------------------------------------------------------
    # OEE Guidelines
    # ------------------------------------------------------------------

    def test_oee_guidelines_evaluation(self) -> None:
        """Should correctly evaluate OEE thresholds with classification labels."""
        # A=95 (Excellent), P=90 (Good), Q=75 (Critical)
        guidelines = self.engine._get_oee_guidelines(95.0, 90.0, 75.0)
        self.assertIn("[Excellent]", guidelines)
        self.assertIn("[Good]", guidelines)
        self.assertIn("[Critical]", guidelines)

    def test_oee_guidelines_needs_attention(self) -> None:
        """Should classify metrics in the Needs Attention band."""
        guidelines = self.engine._get_oee_guidelines(70.0, 85.0, 95.0)
        self.assertIn("[Needs Attention]", guidelines)

    def test_find_band_returns_tuple(self) -> None:
        """_find_band should return (classification, rationale) tuple."""
        a_bands = (
            self.engine.oee_guidelines
            .get("availability_thresholds", {})
            .get("bands", [])
        )
        classification, rationale = self.engine._find_band(95.0, a_bands)
        self.assertEqual(classification, "Excellent")
        self.assertIn("world-class", rationale.lower())

    # ------------------------------------------------------------------
    # Six Big Losses
    # ------------------------------------------------------------------

    def test_six_big_losses_matching_single(self) -> None:
        """Should return losses for Availability with definition."""
        losses = self.engine._get_six_big_losses("Availability")
        self.assertIn("Breakdown Losses", losses)
        self.assertIn("Setup and Adjustment", losses)
        self.assertIn("Definition:", losses)
        self.assertIn("Typical Causes:", losses)
        self.assertNotIn("Small Stops", losses)

    def test_six_big_losses_matching_mixed(self) -> None:
        """Should return matching losses for Mixed Loss patterns."""
        losses = self.engine._get_six_big_losses(
            "Mixed Loss - Availability (18.75%) + Performance (17.95%)"
        )
        self.assertIn("Breakdown Losses", losses)
        self.assertIn("Small Stops", losses)

    def test_six_big_losses_no_match(self) -> None:
        """No Significant Loss should return fallback text."""
        losses = self.engine._get_six_big_losses("No Significant Loss")
        self.assertIn("No specific Six Big Loss", losses)

    # ------------------------------------------------------------------
    # Full Context Building
    # ------------------------------------------------------------------

    def test_build_record_context(self) -> None:
        """Should successfully build a comprehensive text context."""
        record = {
            "machine_id": "Press_Line_1",
            "shift": "Morning",
            "error_code": "DT-01",
            "description": "Mechanical Breakdown",
            "typical_downtime": "30-240",
            "availability": 70.0,
            "performance": 95.0,
            "quality": 99.0,
            "availability_loss": "30.00%",
            "performance_loss": "5.00%",
            "quality_loss": "1.00%",
            "oee": "65.83%",
            "dominant_loss": "Availability",
        }

        context = self.engine.build_record_context(record)

        # Verify all sections are present
        self.assertIn("PRODUCTION RECORD", context)
        self.assertIn("Press_Line_1", context)
        self.assertIn("DT-01", context)
        self.assertIn("MACHINE PROFILE", context)
        self.assertIn("MANUFACTURING PLAYBOOK", context)
        self.assertIn("OEE GUIDELINE CLASSIFICATION", context)
        self.assertIn("SIX BIG LOSSES", context)

    def test_context_contains_classification_labels(self) -> None:
        """Built context should contain OEE guideline classification labels."""
        record = {
            "machine_id": "CNC_Milling_3",
            "shift": "Night",
            "error_code": "DT-01",
            "description": "Mechanical Breakdown",
            "typical_downtime": "30-240",
            "availability": 55.0,
            "performance": 92.0,
            "quality": 98.0,
            "availability_loss": "45.00%",
            "performance_loss": "8.00%",
            "quality_loss": "2.00%",
            "oee": "49.59%",
            "dominant_loss": "Availability",
        }

        context = self.engine.build_record_context(record)
        self.assertIn("[Critical]", context)

    def test_context_contains_possible_causes(self) -> None:
        """Built context should include playbook possible causes."""
        record = {
            "machine_id": "Press_Line_1",
            "shift": "Morning",
            "error_code": "DT-01",
            "description": "Mechanical Breakdown",
            "typical_downtime": "30-240",
            "availability": 70.0,
            "performance": 95.0,
            "quality": 99.0,
            "availability_loss": "30.00%",
            "performance_loss": "5.00%",
            "quality_loss": "1.00%",
            "oee": "65.83%",
            "dominant_loss": "Availability",
        }

        context = self.engine.build_record_context(record)
        self.assertIn("Possible Mechanical Causes:", context)
        self.assertIn("Bearing failure", context)


if __name__ == "__main__":
    unittest.main()
