import logging
import json
import os
import pandas as pd
from typing import Dict, Any, Tuple
from copilot.dashboard_context import DashboardContext

logger = logging.getLogger(__name__)

class ScenarioService:
    def simulate(self, scenario_type: str, improvement_pct: float, analytics_context: Dict[str, Any], comp_pcts: Dict[str, float] = None) -> Dict[str, Any]:
        logger.info(f"Running simulation for: {scenario_type} with +{improvement_pct}%")
        
        ctx = DashboardContext(analytics_context)
        current_avail = self._parse_percentage(ctx.availability)
        current_perf = self._parse_percentage(ctx.performance)
        current_qual = self._parse_percentage(ctx.quality)
        current_oee = self._parse_percentage(ctx.oee)
        
        # UI is bugged and passes single-row loss instead of total loss. Override it from the database.
        current_loss = self._parse_currency(ctx.business_loss)
        try:
            biz_path = os.path.join(os.path.dirname(__file__), "..", "debug", "05_business_impact.csv")
            if os.path.exists(biz_path):
                df_biz = pd.read_csv(biz_path)
                if "Estimated Business Loss" in df_biz.columns:
                    current_loss = round(float(df_biz["Estimated Business Loss"].sum()), 2)
        except Exception as e:
            logger.error(f"Failed to read true business loss: {e}")

        if current_oee == 0:
            return {"error": "Cannot run simulation: Current OEE is 0 or invalid in the dashboard."}
            
        if scenario_type == "compare_all":
            results = {
                "current": {
                    "Availability": current_avail,
                    "Performance": current_perf,
                    "Quality": current_qual,
                    "OEE": current_oee,
                    "Business Loss": current_loss
                },
                "scenarios": {},
                "best_scenario": None,
                "improvement_pct": improvement_pct
            }
            
            best_savings = -1
            best_name = ""
            
            for stype in ["availability", "performance", "quality"]:
                pct = comp_pcts.get(stype, improvement_pct) if comp_pcts else improvement_pct
                res = self._run_single_scenario(stype, pct, current_avail, current_perf, current_qual, current_oee, current_loss)
                if "error" in res:
                    results["scenarios"][stype.capitalize()] = res
                    continue
                res["applied_pct"] = pct
                results["scenarios"][stype.capitalize()] = res
                if res["Savings"] > best_savings:
                    best_savings = res["Savings"]
                    best_name = stype.capitalize()
                    
            results["best_scenario"] = best_name
            return results
            
        else:
            res = self._run_single_scenario(scenario_type, improvement_pct, current_avail, current_perf, current_qual, current_oee, current_loss)
            res["current"] = {
                "Availability": current_avail,
                "Performance": current_perf,
                "Quality": current_qual,
                "OEE": current_oee,
                "Business Loss": current_loss
            }
            res["scenario_type"] = scenario_type.capitalize()
            res["improvement_pct"] = improvement_pct
            return res

    def _run_single_scenario(self, scenario_type, pct, c_a, c_p, c_q, c_oee, c_loss):
        p_a, p_p, p_q = c_a, c_p, c_q
        
        if scenario_type == "availability":
            p_a = c_a + pct
            if p_a > 100.0:
                return {"error": f"Infeasible: Projected Availability exceeds 100% ({p_a:.2f}%)."}
        elif scenario_type == "performance":
            p_p = c_p + pct
            if p_p > 100.0:
                return {"error": f"Infeasible: Projected Performance exceeds 100% ({p_p:.2f}%)."}
        elif scenario_type == "quality":
            p_q = c_q + pct
            if p_q > 100.0:
                return {"error": f"Infeasible: Projected Quality exceeds 100% ({p_q:.2f}%)."}
            
        p_oee = (p_a / 100.0) * (p_p / 100.0) * (p_q / 100.0) * 100.0
        
        current_gap = 100.0 - c_oee
        if current_gap <= 0:
            p_loss = 0.0
            savings = 0.0
        else:
            proj_gap = 100.0 - p_oee
            p_loss = c_loss * (proj_gap / current_gap)
            savings = c_loss - p_loss
            
        return {
            "Projected Availability": p_a,
            "Projected Performance": p_p,
            "Projected Quality": p_q,
            "Projected OEE": p_oee,
            "Projected Business Loss": p_loss,
            "Savings": savings
        }

    def _parse_percentage(self, val_str: str) -> float:
        try:
            return float(str(val_str).replace("%", "").strip())
        except ValueError:
            return 0.0

    def _parse_currency(self, val_str: str) -> float:
        try:
            # Remove common currency symbols and commas
            cl = str(val_str).replace("₹", "").replace("$", "").replace("€", "").replace("£", "").replace("?", "").replace(",", "").strip()
            return float(cl)
        except ValueError:
            return 0.0
