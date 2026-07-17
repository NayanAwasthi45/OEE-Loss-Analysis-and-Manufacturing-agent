import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Handles presentation and reporting of OEE metrics,
    separating business logic from presentation.
    """
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
    
    def display_summary(self, df: pd.DataFrame) -> None:
        """
        Displays a concise analytics summary of the OEE metrics.
        """
        logger.info("Generating concise analytics summary.")
        if df.empty:
            print("\nNo data available to display.")
            return
            
        print("\n" + "="*40)
        print(" OEE Analytics Summary ")
        print("="*40)
        
        average_oee = df["OEE"].mean()
        print(f"Overall Average OEE: {average_oee:.2f}%\n")
        
        # Calculate machine-level statistics
        machine_oee = df.groupby("Machine ID")["OEE"].mean()
        
        highest_machine = machine_oee.idxmax()
        highest_oee = machine_oee.max()
        
        lowest_machine = machine_oee.idxmin()
        lowest_oee = machine_oee.min()
        
        print("--- Machine Performance ---")
        print(f"Top Performer:    {highest_machine} ({highest_oee:.2f}%)")
        print(f"Lowest Performer: {lowest_machine} ({lowest_oee:.2f}%)\n")
        
        print("--- Global Key Metrics (Averages) ---")
        avg_availability = df["Availability"].mean()
        avg_performance = df["Performance"].mean()
        avg_quality = df["Quality"].mean()
        print(f"Availability: {avg_availability:.2f}%")
        print(f"Performance:  {avg_performance:.2f}%")
        print(f"Quality:      {avg_quality:.2f}%")
        print("="*40 + "\n")
        
        if self.debug_mode:
            self._display_full_table(df)
            
    def _display_full_table(self, df: pd.DataFrame) -> None:
        """
        Displays the full DataFrame for debugging purposes.
        """
        logger.info("Generating full data table for debugging.")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print("\n--- Full OEE Results Table (Debugging) ---")
        print(df)
        print("-" * 40 + "\n")
