"""
OEE Calculator for the Manufacturing Analytics Assistant.

Performs 100% deterministic calculations for:
- Availability, Performance, Quality, OEE
- Availability Loss, Performance Loss, Quality Loss
- Dominant Loss classification with Mixed Loss and
  No Significant Loss thresholds
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class OEECalculator:
    """
    Calculates OEE (Overall Equipment Effectiveness) metrics and
    deterministic loss classifications.

    All calculations are 100% deterministic — no LLM involvement.
    """

    # If the top two pillar losses differ by less than this threshold,
    # the loss is classified as Mixed Loss.
    MIXED_LOSS_THRESHOLD: float = 5.0

    # If the highest pillar loss is below this threshold, the record
    # is classified as "No Significant Loss" instead of Mixed Loss.
    # Prevents DT-00 / healthy records from becoming "Mixed Loss".
    NO_SIGNIFICANT_LOSS_THRESHOLD: float = 8.0

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates Availability, Performance, Quality, OEE, pillar losses,
        and dominant loss classification.

        Args:
            df: The validated production DataFrame. Must contain:
                - Planned Time (min)
                - Downtime (min)
                - Total Parts Produced
                - Defective Parts
                - Ideal Cycle Time (min/unit)

        Returns:
            A new DataFrame with calculated OEE metrics, loss columns,
            and Dominant Loss classification appended.
        """
        logger.info("Starting OEE calculation.")

        calc_df = df.copy()

        planned_time = calc_df["Planned Time (min)"]
        downtime = calc_df["Downtime (min)"]
        total_parts = calc_df["Total Parts Produced"]
        defective_parts = calc_df["Defective Parts"]
        ideal_cycle_time = calc_df["Ideal Cycle Time (min/unit)"]

        # Operating Time
        operating_time = planned_time - downtime

        # Availability = (Planned - Downtime) / Planned
        availability = np.where(planned_time > 0, operating_time / planned_time, 0)

        # Performance = (Parts * Ideal Cycle Time) / Operating Time
        performance = np.where(
            operating_time > 0,
            (total_parts * ideal_cycle_time) / operating_time,
            0,
        )

        # Quality = (Parts - Defects) / Parts
        quality = np.where(
            total_parts > 0, (total_parts - defective_parts) / total_parts, 0
        )

        # OEE = A * P * Q
        oee = availability * performance * quality

        # Core OEE metrics (percentages)
        calc_df["Availability"] = (availability * 100).round(2)
        calc_df["Performance"] = (performance * 100).round(2)
        calc_df["Quality"] = (quality * 100).round(2)
        calc_df["OEE"] = (oee * 100).round(2)

        # Pillar losses (percentage points lost from 100%)
        calc_df["Availability Loss"] = (100.0 - calc_df["Availability"]).round(2)
        calc_df["Performance Loss"] = (100.0 - calc_df["Performance"]).round(2)
        calc_df["Quality Loss"] = (100.0 - calc_df["Quality"]).round(2)

        # Dominant loss classification
        calc_df["Dominant Loss"] = calc_df.apply(self._get_dominant_loss, axis=1)

        logger.info("OEE calculation completed.")
        return calc_df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_dominant_loss(self, row: pd.Series) -> str:
        """
        Returns the dominant loss pillar with intelligent thresholds.

        Logic:
        1. If the highest pillar loss < NO_SIGNIFICANT_LOSS_THRESHOLD (8%),
           return 'No Significant Loss'. This prevents healthy records
           (e.g., DT-00) from being incorrectly classified as Mixed Loss.

        2. If the top two pillar losses differ by < MIXED_LOSS_THRESHOLD (5%),
           return 'Mixed Loss - PillarA (X%) + PillarB (Y%)'.

        3. Otherwise, return the single dominant pillar name.

        Args:
            row: A DataFrame row containing Availability Loss,
                 Performance Loss, and Quality Loss.

        Returns:
            Dominant loss classification string.
        """
        losses = {
            "Availability": row["Availability Loss"],
            "Performance": row["Performance Loss"],
            "Quality": row["Quality Loss"],
        }
        sorted_losses = sorted(losses.items(), key=lambda x: x[1], reverse=True)
        first_name, first_val = sorted_losses[0]
        second_name, second_val = sorted_losses[1]

        # Threshold 1: No significant loss
        if first_val < self.NO_SIGNIFICANT_LOSS_THRESHOLD:
            return "No Significant Loss"

        # Threshold 2: Mixed loss (top two are close)
        if (first_val - second_val) < self.MIXED_LOSS_THRESHOLD:
            return (
                f"Mixed Loss - {first_name} ({first_val:.2f}%) "
                f"+ {second_name} ({second_val:.2f}%)"
            )

        # Clear dominant pillar
        return first_name
