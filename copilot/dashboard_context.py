from typing import Dict, Any, Optional

class DashboardContext:
    """
    Parses and formats the current dashboard context coming from the UI.
    Provides utility methods to format it for the LLM.
    """
    def __init__(self, raw_context: Optional[Dict[str, Any]]):
        self.raw_context = raw_context or {}
        
    @property
    def machine(self) -> str:
        return self.raw_context.get("Machine", "N/A")
        
    @property
    def oee(self) -> str:
        # Check if it's already a string with %, or a float
        val = self.raw_context.get("Average OEE", "N/A")
        if isinstance(val, (int, float)):
            return f"{round(val, 2)}%"
        return str(val)
        
    @property
    def availability(self) -> str:
        val = self.raw_context.get("Average Availability", "N/A")
        if isinstance(val, (int, float)):
            return f"{round(val, 2)}%"
        return str(val)

    @property
    def performance(self) -> str:
        val = self.raw_context.get("Average Performance", "N/A")
        if isinstance(val, (int, float)):
            return f"{round(val, 2)}%"
        return str(val)
        
    @property
    def quality(self) -> str:
        val = self.raw_context.get("Average Quality", "N/A")
        if isinstance(val, (int, float)):
            return f"{round(val, 2)}%"
        return str(val)

    @property
    def business_loss(self) -> str:
        val = self.raw_context.get("Estimated Business Loss", "N/A")
        if isinstance(val, (int, float)):
            return f"₹{val:,.2f}"
        return str(val)
        
    @property
    def root_cause(self) -> str:
        return self.raw_context.get("AI Root Cause", "N/A")

    def to_formatted_text(self) -> str:
        """Converts the context to a clean string for LLM injection."""
        if not self.raw_context:
            return "No active dashboard analysis context."
            
        return "\n".join([f"- {k}: {v}" for k, v in self.raw_context.items()])
