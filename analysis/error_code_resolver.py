"""
Error Code Resolver for the Manufacturing Analytics Assistant.

Resolves manufacturing Error Codes into runtime-visible knowledge
using the error_codes.json knowledge base. Only exposes Description
and Typical Downtime — Business Meaning and OEE Impact remain
internal knowledge and are not propagated to outputs.

This is a purely deterministic lookup — no LLM required.
"""

import json
import pandas as pd
import logging
from config import ERROR_CODES_PATH

logger = logging.getLogger(__name__)


class ErrorCodeResolver:
    """
    Resolves manufacturing Error Codes into structured knowledge
    using the error_codes.json knowledge base.

    Enriches DataFrames with Description and Typical Downtime only.
    Business Meaning and OEE Impact are internal knowledge fields
    and are NOT exposed to prevent redundant output.
    """

    def __init__(self, knowledge_path: str = ERROR_CODES_PATH) -> None:
        """
        Loads the error code knowledge base from disk.

        Args:
            knowledge_path: Absolute path to the error_codes.json file.
        """
        logger.info(f"Loading error code knowledge base from: {knowledge_path}")
        with open(knowledge_path, "r", encoding="utf-8") as f:
            self._knowledge: dict = json.load(f)
        logger.info(f"Loaded {len(self._knowledge)} error code definitions.")

    @property
    def valid_codes(self) -> set:
        """Returns the set of known error codes."""
        return set(self._knowledge.keys())

    def resolve(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Appends Description and Typical Downtime columns to the DataFrame
        by looking up each Error Code in the knowledge base.

        Business Meaning and OEE Impact are intentionally excluded —
        they are internal knowledge fields that create redundant output
        when combined with deterministic loss calculations.

        Args:
            df: DataFrame that must contain an 'Error Code' column.

        Returns:
            A new DataFrame with two additional columns:
            - Description
            - Typical Downtime

        Raises:
            ValueError: If any Error Code is not found in the knowledge base.
        """
        logger.info("Resolving error codes to operational knowledge.")
        resolved_df = df.copy()

        descriptions: list[str] = []
        typical_downtimes: list[str] = []

        for _, row in resolved_df.iterrows():
            code = row["Error Code"]
            entry = self._knowledge.get(code)
            if entry is None:
                raise ValueError(
                    f"Unknown Error Code '{code}' not found in knowledge base."
                )
            descriptions.append(entry["description"])
            typical_downtimes.append(entry["typical_downtime"])

        resolved_df["Description"] = descriptions
        resolved_df["Typical Downtime"] = typical_downtimes

        logger.info("Error code resolution completed.")
        return resolved_df
