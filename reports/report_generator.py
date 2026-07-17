"""
Report Generator for the Manufacturing Analytics Assistant.

Displays a structured console summary with query context, OEE metrics,
and AI processing statistics. Separates presentation from business logic.
"""

import pandas as pd
import logging
from typing import Optional

from core.query_parser import QueryFilter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Handles presentation and console reporting of OEE metrics.

    Displays a structured summary including:
    - Query context (Machine, Shift, Date)
    - Records processed count
    - OEE statistics (Average, Highest, Lowest)
    - Pillar averages (Availability, Performance, Quality)
    - AI processing statistics (Processed, Skipped, Response Time)
    """

    def __init__(self, debug_mode: bool = False) -> None:
        """
        Initializes the ReportGenerator.

        Args:
            debug_mode: If True, displays the full DataFrame table.
        """
        self.debug_mode = debug_mode

    def display_summary(
        self,
        df: pd.DataFrame,
        query_filter: Optional[QueryFilter] = None,
        ai_processed: int = 0,
        ai_skipped: int = 0,
        groq_response_time: float = 0.0,
    ) -> None:
        """
        Displays a structured manufacturing analytics console summary.

        Args:
            df: The fully enriched DataFrame with OEE metrics and AI analysis.
            query_filter: The parsed query filter (for context display).
            ai_processed: Number of records sent to AI analysis.
            ai_skipped: Number of healthy records skipped.
            groq_response_time: Total Groq API response time in seconds.
        """
        logger.info("Generating manufacturing analytics summary.")

        if df.empty:
            print("\n  No matching production records found.")
            print("  Please check your filter criteria and try again.\n")
            return

        # Extract query context
        machine = query_filter.machine_id if query_filter and query_filter.machine_id else "All"
        shift = query_filter.shift if query_filter and query_filter.shift else "All"
        date = query_filter.date if query_filter and query_filter.date else "All"

        # Calculate statistics
        records_count = len(df)
        avg_oee = df["OEE"].mean()
        max_oee = df["OEE"].max()
        min_oee = df["OEE"].min()
        avg_availability = df["Availability"].mean()
        avg_performance = df["Performance"].mean()
        avg_quality = df["Quality"].mean()

        # Calculate business impact statistics if available
        has_business_impact = "Estimated Business Loss" in df.columns
        if has_business_impact:
            total_loss = df["Estimated Business Loss"].sum()
            avg_loss = df["Estimated Business Loss"].mean()
            max_loss = df["Estimated Business Loss"].max()
            if max_loss > 0:
                highest_machine = df.loc[df["Estimated Business Loss"].idxmax(), "Machine ID"]
            else:
                highest_machine = "N/A"

        # Display formatted summary
        separator = "═" * 56
        thin_sep = "─" * 56

        print(f"\n  {separator}")
        print(f"    Manufacturing Analytics Report")
        print(f"  {separator}")
        print(f"    Records Processed:     {records_count}")
        print(f"    Machine:               {machine}")
        print(f"    Shift:                 {shift}")
        print(f"    Date:                  {date}")
        print(f"  {thin_sep}")
        print(f"    Average OEE:           {avg_oee:.2f}%")
        print(f"    Highest OEE:           {max_oee:.2f}%")
        print(f"    Lowest OEE:            {min_oee:.2f}%")
        print(f"  {thin_sep}")
        print(f"    Average Availability:  {avg_availability:.2f}%")
        print(f"    Average Performance:   {avg_performance:.2f}%")
        print(f"    Average Quality:       {avg_quality:.2f}%")
        print(f"  {thin_sep}")
        print(f"    AI Processed Records:  {ai_processed}")
        print(f"    AI Skipped Records:    {ai_skipped}")
        print(f"    Groq Response Time:    {groq_response_time:.2f}s")
        if has_business_impact:
            print(f"  {thin_sep}")
            print(f"    Total Estimated Loss:  ₹{total_loss:,.2f}")
            print(f"    Average Business Loss: ₹{avg_loss:,.2f}")
            print(f"    Highest Business Loss: ₹{max_loss:,.2f}")
            print(f"    Highest Prio. Machine: {highest_machine}")
        print(f"  {separator}\n")

        if self.debug_mode:
            self._display_debug_table(df)

    def _display_debug_table(self, df: pd.DataFrame) -> None:
        """
        Displays the full DataFrame for debugging purposes.

        Shows only the key analysis columns to keep output readable.
        """
        logger.info("Generating debug data table.")

        display_cols = [
            col for col in [
                "Machine ID", "Shift", "Date", "Error Code",
                "OEE", "Availability", "Performance", "Quality",
                "Dominant Loss", "AI Validation", "Validation Reason", "Likely Root Cause", "Manufacturing Insight",
            ]
            if col in df.columns
        ]

        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        pd.set_option("display.max_colwidth", 40)
        print("\n  --- Debug: Key Analysis Columns ---")
        print(df[display_cols].to_string(index=False))
        print(f"  {'─' * 56}\n")
