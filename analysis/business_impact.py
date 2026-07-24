"""
Business Impact Engine for the Manufacturing Analytics Assistant.

Converts operational OEE metrics into financial business impact.
Calculates production loss, downtime cost, scrap cost, estimated business
loss, and prioritizes records based on a weighted scoring model.
"""

import os
import json
import logging
import pandas as pd
import numpy as np

from config import BUSINESS_CONFIG_PATH

logger = logging.getLogger(__name__)


class BusinessImpactEngine:
    """
    Translates deterministic OEE metrics into actionable financial
    and operational business impact.
    """

    def __init__(self) -> None:
        """Initializes the engine and loads configurable cost assumptions."""
        self.downtime_cost_per_minute = 400.0
        self.scrap_cost_per_part = 120.0
        self.production_value_per_part = 250.0

        self._load_config()

    def _load_config(self) -> None:
        """Loads business configuration from JSON."""
        if not os.path.exists(BUSINESS_CONFIG_PATH):
            logger.warning(
                f"Business config not found at {BUSINESS_CONFIG_PATH}. "
                f"Using default assumptions."
            )
            return

        try:
            with open(BUSINESS_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.downtime_cost_per_minute = float(
                    config.get("downtime_cost_per_minute", self.downtime_cost_per_minute)
                )
                self.scrap_cost_per_part = float(
                    config.get("scrap_cost_per_part", self.scrap_cost_per_part)
                )
                self.production_value_per_part = float(
                    config.get("production_value_per_part", self.production_value_per_part)
                )
            logger.info("Business configuration loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load business configuration: {e}")

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates production loss, financial impact, and priority score.

        Args:
            df: DataFrame containing OEE and operational metrics.

        Returns:
            A new DataFrame enriched with business impact metrics.
        """
        logger.info("Calculating Business Impact metrics.")

        if df.empty:
            logger.warning("Empty dataframe provided to BusinessImpactEngine.")
            return df

        result_df = df.copy()

        # Safely extract operational inputs
        planned_time = result_df["Planned Time (min)"].fillna(0)
        downtime = result_df["Downtime (min)"].fillna(0)
        operating_time = np.maximum(0, planned_time - downtime)
        
        ideal_cycle_time = result_df["Ideal Cycle Time (min/unit)"].replace(0, np.nan)
        total_parts = result_df["Total Parts Produced"].fillna(0)
        defective_parts = result_df["Defective Parts"].fillna(0)

        # 1. Operational Loss Metrics
        expected_production = (planned_time / ideal_cycle_time).fillna(0)
        production_loss = np.maximum(0, expected_production - total_parts)
        
        expected_throughput = (operating_time / ideal_cycle_time).fillna(0)
        throughput_loss = np.maximum(0, expected_throughput - total_parts)

        result_df["Production Loss (units)"] = production_loss.round(0).astype(int)
        result_df["Throughput Loss (units)"] = throughput_loss.round(0).astype(int)

        # 2. Financial Loss Metrics
        downtime_cost = downtime * self.downtime_cost_per_minute
        scrap_cost = defective_parts * self.scrap_cost_per_part
        production_loss_cost = result_df["Production Loss (units)"] * self.production_value_per_part

        estimated_business_loss = downtime_cost + scrap_cost + production_loss_cost

        result_df["Downtime Cost"] = downtime_cost.round(2)
        result_df["Scrap Cost"] = scrap_cost.round(2)
        result_df["Production Loss Cost"] = production_loss_cost.round(2)
        result_df["Estimated Business Loss"] = estimated_business_loss.round(2)

        # 2a. Transparent Calculation Breakdown
        result_df["Business Loss Breakdown"] = result_df.apply(
            lambda r: f"Downtime (₹{r['Downtime Cost']:,.2f}) + "
                      f"Scrap (₹{r['Scrap Cost']:,.2f}) + "
                      f"Prod. Loss (₹{r['Production Loss Cost']:,.2f})",
            axis=1
        )

        # 2b. Primary Business Driver
        def get_primary_driver(row: pd.Series) -> str:
            costs = {
                "Downtime Cost": row["Downtime Cost"],
                "Scrap Cost": row["Scrap Cost"],
                "Production Loss Cost": row["Production Loss Cost"]
            }
            if sum(costs.values()) == 0:
                return "None"
            return max(costs, key=costs.get)

        result_df["Primary Business Driver"] = result_df.apply(get_primary_driver, axis=1)

        # 3. Priority Scoring Model
        self._calculate_priority_score(result_df)

        # 4. Rank records (Highest Business Loss first)
        # We use dense rank on Business Loss (descending)
        result_df["Top Loss Driver Rank"] = result_df["Estimated Business Loss"].rank(
            method="dense", ascending=False
        ).astype(int)

        # Ensure the final output is sorted by rank
        result_df.sort_values(by="Top Loss Driver Rank", inplace=True)
        result_df.reset_index(drop=True, inplace=True)

        logger.info("Business Impact calculations completed.")
        return result_df

    def _calculate_priority_score(self, df: pd.DataFrame) -> None:
        """
        Calculates a 0-100 Priority Score using a weighted model:
        - OEE (30% weight) - Lower OEE yields a higher score
        - Business Loss (40% weight) - Normalized against max loss in dataset
        - Downtime (20% weight) - Normalized against max downtime in dataset
        - Severity (10% weight) - Based on error code severity
        """
        max_loss = df["Estimated Business Loss"].max()
        max_downtime = df["Downtime (min)"].max()

        if pd.isna(max_loss) or max_loss == 0:
            max_loss = 1.0  # Prevent division by zero
        if pd.isna(max_downtime) or max_downtime == 0:
            max_downtime = 1.0

        scores = []
        levels = []

        for _, row in df.iterrows():
            oee = row.get("OEE", 100.0)
            if pd.isna(oee):
                oee = 100.0
                
            loss = row.get("Estimated Business Loss", 0.0)
            if pd.isna(loss):
                loss = 0.0
                
            downtime = row.get("Downtime (min)", 0.0)
            if pd.isna(downtime):
                downtime = 0.0
                
            error_code = str(row.get("Error Code", "DT-00"))

            # Component 1: OEE (Max 30) - Inversely proportional
            oee_score = max(0.0, (100.0 - oee) / 100.0 * 30.0)

            # Component 2: Business Loss (Max 40)
            loss_score = min(40.0, (loss / max_loss) * 40.0)

            # Component 3: Downtime (Max 20)
            downtime_score = min(20.0, (downtime / max_downtime) * 20.0)

            # Component 4: Severity (Max 10)
            severity_score = self._get_severity_score(error_code)

            total_score = round(oee_score + loss_score + downtime_score + severity_score)
            total_score = min(100, max(0, total_score))

            scores.append(total_score)
            levels.append(self._get_priority_level(total_score))

        df["Priority Score"] = scores
        df["Priority"] = levels

    def _get_severity_score(self, error_code: str) -> float:
        """Returns a predefined severity score based on the error code."""
        if error_code == "DT-01":
            return 10.0  # Critical - Breakdown
        elif error_code in ["DT-02", "DT-03"]:
            return 8.0   # High - Electrical/Changeover
        elif error_code in ["DT-05", "DT-06", "DT-07"]:
            return 6.0   # Medium - Speed/Quality drops
        elif error_code == "DT-04":
            return 4.0   # Low - Small Stops
        return 0.0       # DT-00 or healthy

    def _get_priority_level(self, score: int) -> str:
        """Translates numerical score into categorical priority level."""
        if score >= 80:
            return "Critical"
        elif score >= 60:
            return "High"
        elif score >= 40:
            return "Medium"
        return "Low"
