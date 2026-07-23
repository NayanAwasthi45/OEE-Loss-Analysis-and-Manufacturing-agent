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
        
        if scenario_type == "compare_all":
            results = {
                "scenarios": {},
                "best_scenario": None,
                "improvement_pct": improvement_pct
            }
            
            # Run one scenario first to get the baseline for the plant
            temp_res = self._run_single_scenario("availability", 0)
            if "error" not in temp_res:
                results["current"] = temp_res["current"]
            
            best_savings = -1
            best_name = ""
            
            for stype in ["availability", "performance", "quality"]:
                pct = comp_pcts.get(stype, improvement_pct) if comp_pcts else improvement_pct
                res = self._run_single_scenario(stype, pct)
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
            res = self._run_single_scenario(scenario_type, improvement_pct)
            res["scenario_type"] = scenario_type.capitalize()
            res["improvement_pct"] = improvement_pct
            return res

    def _run_single_scenario(self, scenario_type, pct):
        biz_path = os.path.join(os.path.dirname(__file__), "..", "debug", "05_business_impact.csv")
        val_path = os.path.join(os.path.dirname(__file__), "..", "debug", "02_validated_data.csv")
        
        try:
            df_biz = pd.read_csv(biz_path)
            df_val = pd.read_csv(val_path)
        except Exception as e:
            logger.error(f"Failed to read CSV files for simulation: {e}")
            return {"error": "Dataset missing for deterministic simulation."}

        # Calculate Plant Baseline
        planned = float(df_val['Planned Time (min)'].sum())
        downtime = float(df_val['Downtime (min)'].sum())
        op_time = planned - downtime
        c_avail = op_time / planned if planned > 0 else 0.0

        total_parts = float(df_val['Total Parts Produced'].sum())
        df_val['Ideal Operating Time'] = df_val['Ideal Cycle Time (min/unit)'] * df_val['Total Parts Produced']
        ideal_op_time = float(df_val['Ideal Operating Time'].sum())
        c_perf = ideal_op_time / op_time if op_time > 0 else 0.0

        defective = float(df_val['Defective Parts'].sum())
        good = total_parts - defective
        c_qual = good / total_parts if total_parts > 0 else 0.0

        c_oee = c_avail * c_perf * c_qual

        # Baseline Losses
        c_downtime_cost = float(df_biz['Downtime Cost'].sum())
        c_scrap_cost = float(df_biz['Scrap Cost'].sum())
        c_prod_loss_cost = float(df_biz['Production Loss Cost'].sum())
        c_loss = c_downtime_cost + c_scrap_cost + c_prod_loss_cost

        p_a, p_p, p_q = c_avail, c_perf, c_qual
        p_downtime_cost, p_scrap_cost, p_prod_loss_cost = c_downtime_cost, c_scrap_cost, c_prod_loss_cost
        savings = 0.0

        if scenario_type == "availability":
            p_a = min(c_avail + (pct / 100.0), 1.0)
            req_op = p_a * planned
            req_down = planned - req_op
            rec_down = min(max(downtime - req_down, 0), downtime)
            cpm = c_downtime_cost / downtime if downtime > 0 else 0
            est_sav = rec_down * cpm
            p_downtime_cost = max(c_downtime_cost - est_sav, 0)
            savings = est_sav

        elif scenario_type == "performance":
            p_p = min(c_perf + (pct / 100.0), 1.0)
            
            # Since Performance uses Ideal Cycle Time per row, we aggregate recovered units row-by-row
            df_perf = df_val.copy()
            df_perf = df_perf.merge(df_biz[['Machine ID', 'Date', 'Shift', 'Production Loss Cost', 'Production Loss (units)']], 
                                    on=['Machine ID', 'Date', 'Shift'], how='left')
            df_perf['OpTime'] = df_perf['Planned Time (min)'] - df_perf['Downtime (min)']
            df_perf['Current Perf'] = (df_perf['Ideal Cycle Time (min/unit)'] * df_perf['Total Parts Produced']) / df_perf['OpTime']
            df_perf['Current Perf'] = df_perf['Current Perf'].fillna(0)
            df_perf['Target Perf'] = df_perf['Current Perf'] + (pct / 100.0)
            df_perf['Target Perf'] = df_perf['Target Perf'].clip(upper=1.0)
            
            df_perf['Required Production'] = (df_perf['Target Perf'] * df_perf['OpTime']) / df_perf['Ideal Cycle Time (min/unit)']
            df_perf['Additional Units'] = df_perf['Required Production'] - df_perf['Total Parts Produced']
            df_perf['Additional Units'] = df_perf['Additional Units'].clip(lower=0)
            
            df_perf['Recovered Units'] = df_perf[['Additional Units', 'Production Loss (units)']].min(axis=1)
            df_perf['Recovered Units'] = df_perf['Recovered Units'].fillna(0)
            
            df_perf['Loss Per Unit'] = df_perf['Production Loss Cost'] / df_perf['Production Loss (units)']
            df_perf['Loss Per Unit'] = df_perf['Loss Per Unit'].fillna(0)
            
            df_perf['Estimated Saving'] = df_perf['Recovered Units'] * df_perf['Loss Per Unit']
            
            savings = float(df_perf['Estimated Saving'].sum())
            p_prod_loss_cost = max(c_prod_loss_cost - savings, 0)

        elif scenario_type == "quality":
            p_q = min(c_qual + (pct / 100.0), 1.0)
            req_good = p_q * total_parts
            allowed_defects = total_parts - req_good
            rec_defects = min(max(defective - allowed_defects, 0), defective)
            cpd = c_scrap_cost / defective if defective > 0 else 0
            est_sav = rec_defects * cpd
            p_scrap_cost = max(c_scrap_cost - est_sav, 0)
            savings = est_sav
            
        p_oee = p_a * p_p * p_q
        p_loss = p_downtime_cost + p_prod_loss_cost + p_scrap_cost
        
        return {
            "current": {
                "Availability": round(c_avail * 100, 2),
                "Performance": round(c_perf * 100, 2),
                "Quality": round(c_qual * 100, 2),
                "OEE": round(c_oee * 100, 2),
                "Business Loss": round(c_loss, 2)
            },
            "Projected Availability": round(p_a * 100, 2),
            "Projected Performance": round(p_p * 100, 2),
            "Projected Quality": round(p_q * 100, 2),
            "Projected OEE": round(p_oee * 100, 2),
            "Projected Business Loss": round(p_loss, 2),
            "Savings": round(savings, 2)
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
