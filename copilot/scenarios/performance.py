from typing import Dict, Any, List
from .base_scenario import BaseScenarioPlugin

class PerformanceScenario(BaseScenarioPlugin):
    @property
    def scenario_name(self) -> str:
        return "Performance"
        
    @property
    def primary_goal(self) -> str:
        return "Increase production speed."

    @property
    def root_problem(self) -> str:
        return "Speed Loss."

    def get_focus_areas(self) -> List[str]:
        return [
            "Cycle Time Optimization",
            "Machine Speed Optimization",
            "Operator Efficiency",
            "Line Balancing",
            "Minor Stop Reduction",
            "Bottleneck Analysis"
        ]

    def analyze_evidence(self, simulation_math: Dict[str, Any]) -> Dict[str, Any]:
        import pandas as pd
        import os
        
        evidence = {
            "required_recovery_metric": "Production Loss (units)",
            "required_recovery_value": 0.0,
            "dominant_contributors": []
        }
        
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "debug")
        validated_csv = os.path.join(debug_dir, "02_validated_data.csv")
        ai_csv = os.path.join(debug_dir, "04_ai_analysis.csv")
        business_csv = os.path.join(debug_dir, "05_business_impact.csv")
        
        if not os.path.exists(business_csv) or not os.path.exists(validated_csv):
            return evidence
            
        try:
            df_biz = pd.read_csv(business_csv)
            df_ai = pd.read_csv(ai_csv) if os.path.exists(ai_csv) else pd.DataFrame()
            df_val = pd.read_csv(validated_csv)
            
            applied_pct = 5.0
            if "scenarios" in simulation_math and "Performance" in simulation_math["scenarios"]:
                applied_pct = simulation_math["scenarios"]["Performance"].get("applied_pct", 5.0)
            elif "improvement_pct" in simulation_math:
                applied_pct = simulation_math.get("improvement_pct", 5.0)

            if not df_val.empty and not df_biz.empty:
                df_merged = pd.merge(df_val, df_biz, on=["Machine ID", "Date", "Shift"])
                
                machine_gb = df_merged.sort_values(by=["Production Loss Cost", "Production Loss (units)"], ascending=[False, False])
                top_machines = machine_gb.head(2)

                top2_current_loss = 0.0
                top2_estimated_saving = 0.0
                total_recovered = 0.0

                for _, top_row in top_machines.iterrows():
                    # For record-level granularity, include the Date
                    machine_id = f"{top_row['Machine ID']} ({top_row['Date']})"
                    raw_machine_id = str(top_row["Machine ID"])
                    m_planned = float(top_row["Planned Time (min)"])
                    m_downtime = float(top_row["Downtime (min)"])
                    m_prod_loss_cost = float(top_row["Production Loss Cost"])
                    m_total_parts = float(top_row["Total Parts Produced"])
                    m_ideal_cycle = float(top_row["Ideal Cycle Time (min/unit)"])
                    m_prod_loss_units = float(top_row["Production Loss (units)"])
                    raw_error_code = str(top_row.get("Error Code", ""))
                    if raw_error_code.startswith("DT-") or raw_error_code.startswith("DEF-"):
                        error_code = "N/A (Speed Loss)"
                    else:
                        error_code = raw_error_code if raw_error_code else "N/A (Speed Loss)"
                    
                    top2_current_loss += m_prod_loss_cost
                    
                    # Machine-Specific Deterministic Math
                    m_op = m_planned - m_downtime
                    m_c_perf = (m_ideal_cycle * m_total_parts) / m_op if m_op > 0 else 0.0
                    m_t_perf = min(m_c_perf + (applied_pct / 100.0), 1.0)
                    
                    m_req_prod = (m_t_perf * m_op) / m_ideal_cycle if m_ideal_cycle > 0 else 0.0
                    m_add_units = max(m_req_prod - m_total_parts, 0)
                    m_rec_units = min(m_add_units, m_prod_loss_units)
                    
                    lpu = m_prod_loss_cost / m_prod_loss_units if m_prod_loss_units > 0 else 0.0
                    m_est_saving = m_rec_units * lpu
                    
                    top2_estimated_saving += m_est_saving
                    total_recovered += m_rec_units
                    
                    contributor = {
                        "machine_id": machine_id,
                        "error_code": error_code,
                        "production_loss_contribution": round(m_prod_loss_units, 2),
                        "estimated_business_loss": round(m_prod_loss_cost, 2),
                        "estimated_savings": round(m_est_saving, 2),
                        "projected_loss": round(max(m_prod_loss_cost - m_est_saving, 0), 2),
                        "recovered_value": round(m_rec_units, 2)
                    }

                    # AI Context
                    if not df_ai.empty:
                        ai_match = df_ai[(df_ai["Machine ID"] == raw_machine_id) & (df_ai["Dominant Loss"] == "Performance")]
                        if not ai_match.empty:
                            contributor["ai_validation"] = str(ai_match.iloc[0].get("AI Validation", "Unknown"))
                            contributor["validation_reason"] = str(ai_match.iloc[0].get("Validation Reason", "None"))
                            contributor["likely_root_cause"] = str(ai_match.iloc[0].get("Likely Root Cause", "Unknown"))
                            contributor["manufacturing_insight"] = str(ai_match.iloc[0].get("Manufacturing Insight", "None"))
                        else:
                            contributor["ai_validation"] = "N/A"
                            contributor["validation_reason"] = "No performance AI context found."
                            contributor["likely_root_cause"] = "Speed loss due to minor stops, operator inefficiency, or suboptimal machine settings."
                            contributor["manufacturing_insight"] = "Performance loss typically points to cycle time deviations."

                    evidence["dominant_contributors"].append(contributor)

                evidence["top2_current_loss"] = round(top2_current_loss, 2)
                evidence["top2_estimated_saving"] = round(top2_estimated_saving, 2)
                evidence["top2_projected_loss"] = round(max(top2_current_loss - top2_estimated_saving, 0), 2)
                evidence["required_recovery_value"] = round(total_recovered, 2)
                    
        except Exception as e:
            print(f"Error in analyze_evidence (Performance): {e}")
            
        return evidence

    def get_business_story(self) -> Dict[str, str]:
        return {
            "objective": "Increase Throughput",
            "outcome": "Higher Production Volume, Lower Speed Loss, Faster Manufacturing"
        }

    def get_roadmap(self) -> Dict[str, str]:
        return {
            "Week 1": "Cycle Time Study",
            "Week 2": "Machine Speed Optimization",
            "Week 3": "Minor Stop Analysis",
            "Week 4": "Production Line Balancing"
        }

    def get_recommendation_style(self) -> str:
        return "Only discuss Machine Speed, Cycle Time, Minor Stops, Operator Efficiency, Line Balancing, and Bottlenecks."
        
    def get_risk_assessment(self) -> Dict[str, str]:
        return {
            "Operational Risk": "Medium",
            "Implementation Risk": "Low",
            "Expected Downtime During Rollout": "0 Shifts (Running Adjustment)"
        }
        
    def get_priorities(self) -> Dict[str, str]:
        return {
            "Immediate": "Cycle Time Study",
            "Within 1 Week": "Minor Stop Reduction",
            "Long Term": "Line Balancing"
        }
