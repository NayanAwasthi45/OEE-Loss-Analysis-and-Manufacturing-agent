"""
Query Parser for the OEE Manufacturing Analytics Assistant.

Parses free-text user queries into structured QueryFilter objects
by extracting Machine IDs, Shift keywords, and Date patterns.
Machine ID matching is performed against known IDs from the database
to support case-insensitive partial matching.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger(__name__)

# Valid shift keywords (case-insensitive matching)
VALID_SHIFTS = {"morning", "afternoon", "night"}

# ISO date pattern: YYYY-MM-DD
_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


@dataclass
class QueryFilter:
    """
    Structured representation of a user's production data query.

    At least one field must be populated for the query to be valid.
    """

    machine_id: Optional[str] = None
    shift: Optional[str] = None
    date: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        """Returns True if no filter criteria were extracted."""
        return self.machine_id is None and self.shift is None and self.date is None

    def describe(self) -> str:
        """Returns a human-readable description of the active filters."""
        parts: list[str] = []
        if self.machine_id:
            parts.append(f"Machine: {self.machine_id}")
        if self.shift:
            parts.append(f"Shift: {self.shift}")
        if self.date:
            parts.append(f"Date: {self.date}")
        return " | ".join(parts) if parts else "No filters"


class QueryParser:
    """
    Parses free-text manufacturing queries into structured filters.

    Requires a list of known machine IDs from the database to perform
    case-insensitive matching. Extracts shifts and dates via keyword
    and regex matching respectively.

    Examples:
        'Show Press_Line_5'                     → machine_id='Press_Line_5'
        'Show Press_Line_5 Morning Shift'       → machine_id='Press_Line_5', shift='Morning'
        'Show Press_Line_5 on 2026-06-18'       → machine_id='Press_Line_5', date='2026-06-18'
        'Show CNC_Milling_3 Night Shift'        → machine_id='CNC_Milling_3', shift='Night'
    """

    def __init__(self, known_machines: List[str]) -> None:
        """
        Initializes the parser with known machine IDs from the database.

        Args:
            known_machines: List of valid Machine ID strings.
        """
        self._known_machines = known_machines
        # Build a case-insensitive lookup: lowercase → original
        self._machine_lookup: dict[str, str] = {
            m.lower(): m for m in known_machines
        }
        logger.info(
            f"QueryParser initialized with {len(known_machines)} known machines."
        )

    def parse(self, user_input: str) -> Optional[QueryFilter]:
        """
        Parses a free-text query into a QueryFilter.

        Args:
            user_input: Raw user query string.

        Returns:
            A populated QueryFilter if at least one filter was extracted,
            or None if no valid filters could be determined.
        """
        if not user_input or not user_input.strip():
            logger.warning("Empty query received.")
            return None

        query = user_input.strip()
        logger.info(f"Parsing query: '{query}'")

        machine_id = self._extract_machine_id(query)
        shift = self._extract_shift(query)
        date = self._extract_date(query)

        query_filter = QueryFilter(
            machine_id=machine_id,
            shift=shift,
            date=date,
        )

        if query_filter.is_empty:
            logger.warning(f"No valid filters extracted from query: '{query}'")
            return None

        logger.info(f"Parsed filter: {query_filter.describe()}")
        return query_filter

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_machine_id(self, query: str) -> Optional[str]:
        """
        Extracts a Machine ID from the query by matching against known
        machine IDs (case-insensitive).

        Matches the longest machine ID first to avoid partial matches
        (e.g., 'Press_Line_5' before 'Press_Line').
        """
        query_lower = query.lower()

        # Sort by length descending to match longest ID first
        sorted_machines = sorted(
            self._machine_lookup.keys(), key=len, reverse=True
        )

        for machine_lower in sorted_machines:
            if machine_lower in query_lower:
                original = self._machine_lookup[machine_lower]
                logger.debug(f"Matched machine: '{original}'")
                return original

        return None

    def _extract_shift(self, query: str) -> Optional[str]:
        """
        Extracts a Shift keyword from the query (case-insensitive).

        Recognizes: Morning, Afternoon, Night.
        Returns the shift in Title Case.
        """
        query_lower = query.lower()

        for shift in VALID_SHIFTS:
            # Use word boundary matching to avoid false positives
            pattern = rf"\b{shift}\b"
            if re.search(pattern, query_lower):
                result = shift.capitalize()
                logger.debug(f"Matched shift: '{result}'")
                return result

        return None

    def _extract_date(self, query: str) -> Optional[str]:
        """
        Extracts a date in YYYY-MM-DD format from the query.

        Returns the first date found, or None if no date pattern matches.
        """
        match = _DATE_PATTERN.search(query)
        if match:
            date_str = match.group(1)
            logger.debug(f"Matched date: '{date_str}'")
            return date_str

        return None
