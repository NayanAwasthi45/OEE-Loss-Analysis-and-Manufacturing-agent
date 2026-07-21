import logging
from typing import Dict, Any, Tuple
from .dashboard_context import DashboardContext

logger = logging.getLogger(__name__)

class ScenarioService:
    """
    Deterministically simulates OEE improvements.
    Does not use RAG.
    """

    def simulate(self, scenario_type: str, analytics_context: Dict[str, Any]) -> str:
        """
        Runs the deterministic calculation and returns formatted markdown.
        scenario_type: "availability", "performance", or "quality"
        """
        logger.info(f"Running simulation for: {scenario_type}")
        
        ctx = DashboardContext(analytics_context)
        
        # Parse current values safely
        current_avail = self._parse_percentage(ctx.availability)
        current_perf = self._parse_percentage(ctx.performance)
        current_qual = self._parse_percentage(ctx.quality)
        current_oee = self._parse_percentage(ctx.oee)
        current_loss = self._parse_currency(ctx.business_loss)

        if current_oee == 0:
            return "Cannot run simulation: Current OEE is 0 or invalid in the dashboard."

        # Target Modifiers (10% relative improvement or +10 absolute, let's do +10 absolute capped at 100)
        proj_avail = current_avail
        proj_perf = current_perf
        proj_qual = current_qual
        
        scenario_name = ""
        impact_reasons = ""
        target_kpi_name = ""
        c_kpi = 0.0
        p_kpi = 0.0

        if scenario_type == "availability":
            scenario_name = "Availability Improvement"
            target_kpi_name = "Availability"
            proj_avail = min(100.0, current_avail + 10.0)
            c_kpi = current_avail
            p_kpi = proj_avail
            impact_reasons = "Higher Availability\nReduced Downtime\nHigher Throughput\nLower Cost"
        elif scenario_type == "performance":
            scenario_name = "Performance Improvement"
            target_kpi_name = "Performance"
            proj_perf = min(100.0, current_perf + 10.0)
            c_kpi = current_perf
            p_kpi = proj_perf
            impact_reasons = "Faster Cycle Times\nFewer Minor Stops\nHigher Throughput\nLower Cost"
        elif scenario_type == "quality":
            scenario_name = "Quality Improvement"
            target_kpi_name = "Quality"
            proj_qual = min(100.0, current_qual + 10.0)
            c_kpi = current_qual
            p_kpi = proj_qual
            impact_reasons = "Reduced Scrap\nLess Rework\nHigher First-Pass Yield\nLower Material Cost"
        else:
            return f"Unknown scenario type: {scenario_type}"

        # Recalculate OEE
        proj_oee = (proj_avail / 100) * (proj_perf / 100) * (proj_qual / 100) * 100
        
        # Recalculate Business Loss proportionately to OEE gap
        # Current Gap = 100 - current_oee
        # Projected Gap = 100 - proj_oee
        # New Loss = Current Loss * (Projected Gap / Current Gap)
        current_gap = 100.0 - current_oee
        if current_gap <= 0:
            proj_loss = 0.0
            savings = 0.0
        else:
            proj_gap = 100.0 - proj_oee
            proj_loss = current_loss * (proj_gap / current_gap)
            savings = current_loss - proj_loss

        return self._format_response(
            scenario_name=scenario_name,
            kpi_name=target_kpi_name,
            c_kpi=c_kpi,
            c_oee=current_oee,
            c_loss=current_loss,
            p_kpi=p_kpi,
            p_oee=proj_oee,
            p_loss=proj_loss,
            savings=savings,
            impact_reasons=impact_reasons
        )

    def _parse_percentage(self, val_str: str) -> float:
        try:
            return float(str(val_str).replace("%", "").strip())
        except ValueError:
            return 0.0

    def _parse_currency(self, val_str: str) -> float:
        try:
            return float(str(val_str).replace("₹", "").replace(",", "").strip())
        except ValueError:
            return 0.0

    def _format_response(self, scenario_name, kpi_name, c_kpi, c_oee, c_loss, p_kpi, p_oee, p_loss, savings, impact_reasons) -> str:
        
        return f"""══════════════════════════════

📊 Scenario Simulation

Scenario

{scenario_name}

══════════════════════════════

Current

{kpi_name}

{c_kpi:.1f}%

OEE

{c_oee:.1f}%

Business Loss

₹{c_loss:,.2f}

══════════════════════════════

Projected

{kpi_name}

{p_kpi:.1f}%

OEE

{p_oee:.1f}%

Business Loss

₹{p_loss:,.2f}

══════════════════════════════

💰 Estimated Savings

₹{savings:,.2f}

══════════════════════════════

🎯 Business Impact

{impact_reasons}
"""
