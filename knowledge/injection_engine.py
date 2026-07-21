"""
Knowledge Injection Engine for the Manufacturing Analytics Assistant.

Loads domain knowledge from JSON files and constructs a rich, text-based
context prompt for the LLM. Ensures the LLM receives specific machine
profiles, playbook entries, OEE guidelines, and Six Big Loss details
tailored to the current production record.
"""

import json
import logging
import os
import threading
from typing import Dict, Any, Optional

from config import KNOWLEDGE_DIR

logger = logging.getLogger(__name__)


class KnowledgeInjectionEngine:
    """
    Loads domain knowledge once into memory and constructs tailored
    LLM prompts for each production record.

    Each context block is designed to be token-efficient while providing
    enough manufacturing reasoning context for the LLM to produce
    expert-level validation and insight.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(KnowledgeInjectionEngine, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, '_initialized', False):
            return
            
        """Loads all domain knowledge JSON files into memory."""
        """Loads all domain knowledge JSON files into memory."""
        self.domain_dir = os.path.join(KNOWLEDGE_DIR, "Domain_knowledge")

        logger.info("Initializing Knowledge Injection Engine...")
        self.machine_profiles = self._load_json("machine_profiles.json")
        self.playbook = self._load_json("manufacturing_playbook.json")
        self.oee_guidelines = self._load_json("oee_guidelines.json")
        self.six_big_losses = self._load_json("six_big_losses.json")
        self._initialized = True
        logger.info("Domain knowledge loaded successfully.")

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Helper to load a JSON file from the Domain_knowledge directory."""
        filepath = os.path.join(self.domain_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load knowledge file {filename}: {e}")
            return {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_record_context(self, record: Dict[str, Any]) -> str:
        """
        Constructs a structured text prompt for a single production record
        by injecting relevant domain knowledge.

        Args:
            record: Dictionary containing the production metrics and
                    error code details.

        Returns:
            Formatted string containing the record data and injected
            knowledge context.
        """
        machine_id = record.get("machine_id", "")
        error_code = record.get("error_code", "")
        dominant_loss = record.get("dominant_loss", "")
        availability = float(record.get("availability", 0))
        performance = float(record.get("performance", 0))
        quality = float(record.get("quality", 0))

        # 1. Machine Profile
        machine_profile_text = self._get_machine_profile(machine_id)

        # 2. Playbook Entry
        playbook_text = self._get_playbook_entry(error_code)

        # 3. OEE Guidelines (with classification labels)
        oee_guidelines_text = self._get_oee_guidelines(
            availability, performance, quality
        )

        # 4. Six Big Losses
        six_big_losses_text = self._get_six_big_losses(dominant_loss)

        context = f"""
=== PRODUCTION RECORD ===
Machine: {machine_id}
Shift: {record.get("shift", "")}
Error Code: {error_code}
Description: {record.get("description", "")}
Typical Downtime Range: {record.get("typical_downtime", "")} min

=== OEE METRICS ===
Availability: {availability:.2f}% (Loss: {record.get("availability_loss", "")})
Performance: {performance:.2f}% (Loss: {record.get("performance_loss", "")})
Quality: {quality:.2f}% (Loss: {record.get("quality_loss", "")})
OEE: {record.get("oee", "")}
Dominant Loss Pillar: {dominant_loss}

=== MACHINE PROFILE ===
{machine_profile_text}

=== MANUFACTURING PLAYBOOK ({error_code}) ===
{playbook_text}

=== OEE GUIDELINE CLASSIFICATION ===
{oee_guidelines_text}

=== SIX BIG LOSSES ===
{six_big_losses_text}
"""
        return context

    # ------------------------------------------------------------------
    # Machine Profile
    # ------------------------------------------------------------------

    def _get_machine_profile(self, machine_id: str) -> str:
        """
        Detects machine family from the Machine ID and returns a concise
        profile including purpose, expected behaviour, failure modes,
        and degradation indicators.
        """
        profiles = self.machine_profiles.get("machine_profiles", [])

        family = self._detect_machine_family(machine_id)

        for profile in profiles:
            if profile.get("machine_type") == family:
                purpose = profile.get("machine_purpose", "")
                behaviour = profile.get("expected_operating_behaviour", "")
                failures = profile.get("common_failure_modes", [])[:4]
                degradation = profile.get(
                    "performance_degradation_indicators", []
                )[:3]

                return (
                    f"Machine Type: {family}\n"
                    f"Purpose: {purpose}\n"
                    f"Expected Operating Behaviour: {behaviour}\n"
                    f"Common Failure Modes: {'; '.join(failures)}\n"
                    f"Degradation Indicators: {'; '.join(degradation)}"
                )

        return "Machine Type: Unknown (no specific profile matched)"

    def _detect_machine_family(self, machine_id: str) -> str:
        """Extracts machine family from the Machine ID string."""
        lower_id = machine_id.lower()
        if "press" in lower_id:
            return "Press Line"
        elif "cnc" in lower_id or "milling" in lower_id:
            return "CNC Milling"
        elif "assembly" in lower_id:
            return "Assembly Line"
        return ""

    # ------------------------------------------------------------------
    # Manufacturing Playbook
    # ------------------------------------------------------------------

    def _get_playbook_entry(self, error_code: str) -> str:
        """
        Returns the playbook entry for the given error code, including
        expected OEE behaviour, impact descriptions, and possible
        operational/mechanical causes that the LLM can use as root-cause
        candidates.
        """
        entries = self.playbook.get("error_codes", [])
        for entry in entries:
            if entry.get("error_code") == error_code:
                # Gather possible causes for root-cause inference
                op_causes = entry.get("possible_operational_causes", [])[:3]
                mech_causes = entry.get("possible_mechanical_causes", [])[:3]
                elec_causes = entry.get("possible_electrical_causes", [])[:2]
                symptoms = entry.get("common_machine_symptoms", [])[:3]

                text = (
                    f"Error Code: {entry.get('error_code')}\n"
                    f"Loss Category: {entry.get('category')}\n"
                    f"Manufacturing Description: "
                    f"{entry.get('manufacturing_description')}\n"
                    f"Expected OEE Behaviour: "
                    f"{entry.get('expected_oee_behaviour')}\n"
                    f"Expected Availability Impact: "
                    f"{entry.get('expected_availability_impact')}\n"
                    f"Expected Performance Impact: "
                    f"{entry.get('expected_performance_impact')}\n"
                    f"Expected Quality Impact: "
                    f"{entry.get('expected_quality_impact')}\n"
                    f"Typical Symptoms: {'; '.join(symptoms)}"
                )

                if op_causes:
                    text += (
                        f"\nPossible Operational Causes: "
                        f"{'; '.join(op_causes)}"
                    )
                if mech_causes:
                    text += (
                        f"\nPossible Mechanical Causes: "
                        f"{'; '.join(mech_causes)}"
                    )
                if elec_causes:
                    text += (
                        f"\nPossible Electrical Causes: "
                        f"{'; '.join(elec_causes)}"
                    )

                return text

        return "No playbook entry found for this error code."

    # ------------------------------------------------------------------
    # OEE Guidelines
    # ------------------------------------------------------------------

    def _get_oee_guidelines(
        self, a: float, p: float, q: float
    ) -> str:
        """
        Evaluates each OEE pillar against the guideline thresholds and
        returns the classification label and manufacturing rationale.
        """
        result = []

        # Availability
        a_bands = (
            self.oee_guidelines
            .get("availability_thresholds", {})
            .get("bands", [])
        )
        a_class, a_rationale = self._find_band(a, a_bands)
        result.append(
            f"Availability ({a:.2f}%): [{a_class}] — {a_rationale}"
        )

        # Performance
        p_bands = (
            self.oee_guidelines
            .get("performance_thresholds", {})
            .get("bands", [])
        )
        p_class, p_rationale = self._find_band(p, p_bands)
        result.append(
            f"Performance ({p:.2f}%): [{p_class}] — {p_rationale}"
        )

        # Quality
        q_bands = (
            self.oee_guidelines
            .get("quality_thresholds", {})
            .get("bands", [])
        )
        q_class, q_rationale = self._find_band(q, q_bands)
        result.append(
            f"Quality ({q:.2f}%): [{q_class}] — {q_rationale}"
        )

        return "\n".join(result)

    def _find_band(
        self, value: float, bands: list
    ) -> tuple[str, str]:
        """
        Finds the correct classification band for a metric value.

        Returns:
            Tuple of (classification_label, manufacturing_rationale).
        """
        for band in bands:
            range_str = band.get("range", "")
            classification = band.get("classification", "")
            rationale = band.get("manufacturing_rationale", "")

            if range_str.startswith(">="):
                threshold = float(
                    range_str.replace(">=", "").replace("%", "").strip()
                )
                if value >= threshold:
                    return classification, rationale
            elif range_str.startswith("<"):
                threshold = float(
                    range_str.replace("<", "").replace("%", "").strip()
                )
                if value < threshold:
                    return classification, rationale
            elif "-" in range_str:
                parts = range_str.split("-")
                low = float(parts[0].replace("%", "").strip())
                high = float(parts[1].replace("%", "").strip())
                if low <= value <= high:
                    return classification, rationale

        return "Unknown", "No matching guideline band found."

    # ------------------------------------------------------------------
    # Six Big Losses
    # ------------------------------------------------------------------

    def _get_six_big_losses(self, dominant_loss: str) -> str:
        """
        Returns Six Big Loss details matching the dominant loss pillar,
        including the formal definition, typical causes, and symptoms
        so the LLM can reference TPM principles in its reasoning.
        """
        losses = self.six_big_losses.get("six_big_losses", [])
        relevant = []

        pillars_to_match = []
        if "Availability" in dominant_loss:
            pillars_to_match.append("Availability")
        if "Performance" in dominant_loss:
            pillars_to_match.append("Performance")
        if "Quality" in dominant_loss:
            pillars_to_match.append("Quality")

        for loss in losses:
            if loss.get("oee_pillar_affected") in pillars_to_match:
                definition = loss.get("definition", "")
                causes = loss.get("typical_causes", [])[:3]
                symptoms = loss.get("common_symptoms", [])[:3]

                loss_text = (
                    f"TPM Loss Category: {loss.get('loss_name')}\n"
                    f"Definition: {definition}\n"
                    f"Typical Causes: {'; '.join(causes)}\n"
                    f"Common Symptoms: {'; '.join(symptoms)}"
                )
                relevant.append(loss_text)

        if not relevant:
            return (
                "No specific Six Big Loss matched the "
                "Dominant Loss pattern."
            )

        return "\n\n".join(relevant)
