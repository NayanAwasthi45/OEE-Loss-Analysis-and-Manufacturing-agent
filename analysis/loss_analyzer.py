"""
Manufacturing Intelligence Analyzer (formerly Loss Analyzer).

Orchestrates the AI analysis pipeline:
1. Pre-filters records to skip healthy production data
2. Builds LLM payloads for problematic records only
3. Maps AI results back to the full DataFrame
4. Handles rate-limit and fallback responses gracefully

The LLM does NOT classify error codes — classification is deterministic
and handled by OEECalculator. The LLM validates, infers root causes,
and produces concise manufacturing observations.
"""

import pandas as pd
import logging
import time
from typing import Dict, Any

from llm.groq_client import GroqClient

logger = logging.getLogger(__name__)


class LossAnalyzer:
    """
    Orchestrates AI-powered manufacturing intelligence analysis.

    Pre-filters records before calling Groq to ensure only problematic
    production events consume LLM tokens. Healthy records are skipped
    with appropriate metadata.

    Output Columns:
        - AI Validation: Verified | Partially Verified | Mismatch | Skipped
        - Validation Reason: Why the validation received that status
        - Likely Root Cause: Specific operational cause
        - Manufacturing Insight: Brief technical explanation (< 60 words)
    """

    # Thresholds for AI pre-filtering
    OEE_THRESHOLD: float = 85.0
    LOSS_THRESHOLD: float = 5.0

    def __init__(self) -> None:
        from knowledge.injection_engine import KnowledgeInjectionEngine
        self.llm_client = GroqClient()
        self.knowledge_engine = KnowledgeInjectionEngine()
        self.ai_processed_count: int = 0
        self.ai_skipped_count: int = 0
        self.groq_response_time: float = 0.0

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriches the OEE DataFrame with AI validation, root causes,
        and manufacturing observations.

        Only problematic records are sent to the LLM. Healthy records
        are marked as 'AI Skipped'.

        Args:
            df: DataFrame already containing Availability, Performance,
                Quality, OEE, loss columns, Dominant Loss, Description,
                and Typical Downtime (from OEECalculator + ErrorCodeResolver).

        Returns:
            Enriched DataFrame with AI Validation, Validation Reason, Likely Root Cause,
            and Manufacturing Insight columns.
        """
        logger.info("Starting manufacturing intelligence analysis.")

        if df.empty:
            logger.warning("Empty dataframe provided to LossAnalyzer.")
            return df

        result_df = df.copy()

        # ----------------------------------------------------------
        # Step 1: Separate records into AI-eligible and healthy
        # ----------------------------------------------------------
        ai_mask = self._get_ai_eligible_mask(result_df)
        ai_records_df = result_df[ai_mask]
        healthy_records_df = result_df[~ai_mask]

        self.ai_processed_count = len(ai_records_df)
        self.ai_skipped_count = len(healthy_records_df)

        logger.info(
            f"AI filter: {self.ai_processed_count} records for AI analysis, "
            f"{self.ai_skipped_count} healthy records skipped."
        )

        # ----------------------------------------------------------
        # Step 2: Initialize output columns with skip defaults
        # ----------------------------------------------------------
        result_df["AI Validation"] = "Skipped"
        result_df["Validation Reason"] = "Healthy production record. No manufacturing anomalies requiring AI analysis."
        result_df["Likely Root Cause"] = "Not Applicable"
        result_df["Manufacturing Insight"] = "Production metrics remain within expected operating thresholds. No abnormal manufacturing behaviour was detected."

        # ----------------------------------------------------------
        # Step 3: Process AI-eligible records through Groq
        # ----------------------------------------------------------
        if self.ai_processed_count > 0:
            records_payload = self._build_llm_payload(ai_records_df)

            logger.info(f"Sending {len(records_payload)} records for AI analysis.")
            start = time.time()

            analyses = self.llm_client.batch_analyze(records_payload)

            self.groq_response_time = time.time() - start
            logger.info(f"Groq response time: {self.groq_response_time:.2f}s.")

            # Map AI results back to DataFrame
            self._map_ai_results(result_df, ai_records_df, analyses)
        else:
            self.groq_response_time = 0.0
            logger.info("No records require AI analysis. All healthy.")

        logger.info("Manufacturing intelligence analysis completed.")
        return result_df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_ai_eligible_mask(self, df: pd.DataFrame) -> pd.Series:
        """
        Returns a boolean mask identifying records that require AI analysis.

        A record is AI-eligible if it satisfies AT LEAST ONE condition:
        - OEE < 85%
        - Availability Loss > 5%
        - Performance Loss > 5%
        - Quality Loss > 5%
        - Dominant Loss starts with 'Mixed Loss'
        - Error Code != 'DT-00'

        Healthy production records (DT-00, high OEE, low losses)
        are skipped to avoid unnecessary LLM calls.
        """
        mask = (
            (df["OEE"] < self.OEE_THRESHOLD)
            | (df["Availability Loss"] > self.LOSS_THRESHOLD)
            | (df["Performance Loss"] > self.LOSS_THRESHOLD)
            | (df["Quality Loss"] > self.LOSS_THRESHOLD)
            | (df["Dominant Loss"].str.startswith("Mixed Loss"))
            | (df["Error Code"] != "DT-00")
        )
        return mask

    def _build_llm_payload(
        self, ai_df: pd.DataFrame
    ) -> list[dict[str, Any]]:
        """
        Constructs the LLM payload from AI-eligible records by building a rich
        context string using the KnowledgeInjectionEngine.
        """
        records: list[dict[str, Any]] = []
        for idx, row in ai_df.iterrows():
            record_dict = {
                "machine_id": row.get("Machine ID", ""),
                "shift": row.get("Shift", ""),
                "error_code": row.get("Error Code", ""),
                "description": row.get("Description", ""),
                "typical_downtime": row.get("Typical Downtime", ""),
                "availability": row.get("Availability", 0),
                "performance": row.get("Performance", 0),
                "quality": row.get("Quality", 0),
                "availability_loss": f"{row.get('Availability Loss', 0):.2f}%",
                "performance_loss": f"{row.get('Performance Loss', 0):.2f}%",
                "quality_loss": f"{row.get('Quality Loss', 0):.2f}%",
                "oee": f"{row.get('OEE', 0):.2f}%",
                "dominant_loss": row.get("Dominant Loss", ""),
            }
            context_block = self.knowledge_engine.build_record_context(record_dict)
            records.append(
                {
                    "id": str(idx),
                    "knowledge_context": context_block
                }
            )
        return records

    def _map_ai_results(
        self,
        result_df: pd.DataFrame,
        ai_records_df: pd.DataFrame,
        analyses: list[dict[str, Any]],
    ) -> None:
        """
        Maps AI analysis results back to the correct rows in result_df.

        Handles missing or malformed AI responses gracefully.
        """
        analysis_map: Dict[str, dict] = {
            str(a.get("id")): a for a in analyses
        }

        for idx in ai_records_df.index:
            analysis = analysis_map.get(str(idx), {})

            ai_validation = analysis.get("ai_validation", "Skipped")
            validation_reason = analysis.get("validation_reason", "LLM processing failed or returned empty.")
            likely_root_cause = analysis.get("likely_root_cause", "Not Applicable")
            manufacturing_insight = analysis.get(
                "manufacturing_insight", "LLM service unavailable. Manual review required."
            )

            result_df.at[idx, "AI Validation"] = ai_validation
            result_df.at[idx, "Validation Reason"] = validation_reason
            result_df.at[idx, "Likely Root Cause"] = likely_root_cause
            result_df.at[idx, "Manufacturing Insight"] = manufacturing_insight

        # Count how many were actually skipped by rate-limit or fallback
        rate_limited = sum(
            1 for a in analyses
            if a.get("likely_root_cause") == "Rate Limit"
        )
        if rate_limited:
            logger.warning(
                f"{rate_limited} records skipped due to Groq rate limiting."
            )
