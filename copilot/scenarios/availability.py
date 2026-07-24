from typing import Dict, Any, List
from .base_scenario import BaseScenarioPlugin

class AvailabilityScenario(BaseScenarioPlugin):
    @property
    def scenario_name(self) -> str:
        return "Availability"
        
    @property
    def primary_goal(self) -> str:
        return "Increase machine uptime."

    @property
    def root_problem(self) -> str:
        return "Downtime."

    def get_focus_areas(self) -> List[str]:
        return [
            "Preventive Maintenance",
            "Predictive Maintenance",
            "Breakdown Analysis",
            "Changeover Reduction",
            "Spare Parts",
            "Maintenance Planning"
        ]

    def analyze_evidence(self, simulation_math: Dict[str, Any]) -> Dict[str, Any]:
        import pandas as pd
        import os
        
        evidence = {
            "required_recovery_metric": "Downtime (min)",
            "required_recovery_value": 0.0,
            "dominant_contributors": []
        }
        
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "debug")
        validated_csv = os.path.join(debug_dir, "02_validated_data.csv")
        ai_csv = os.path.join(debug_dir, "04_ai_analysis.csv")
        business_csv = os.path.join(debug_dir, "05_business_impact.csv")
        
        if not os.path.exists(validated_csv):
            return evidence
            
        try:
            df_val = pd.read_csv(validated_csv)
            df_ai = pd.read_csv(ai_csv) if os.path.exists(ai_csv) else pd.DataFrame()
            df_biz = pd.read_csv(business_csv) if os.path.exists(business_csv) else pd.DataFrame()
            
            applied_pct = 5.0
            if "scenarios" in simulation_math and "Availability" in simulation_math["scenarios"]:
                applied_pct = simulation_math["scenarios"]["Availability"].get("applied_pct", 5.0)
            elif "improvement_pct" in simulation_math:
                applied_pct = simulation_math.get("improvement_pct", 5.0)

            if not df_val.empty and not df_biz.empty:
                df_merged = pd.merge(df_val, df_biz, on=["Machine ID", "Date", "Shift"])
                
                # 1. Required Recovery Calculation
                if "Planned Time (min)" in df_val.columns:
                    total_planned = float(df_val["Planned Time (min)"].sum())
                    overall_required_recovery = round(total_planned * (applied_pct / 100.0), 2)
                    evidence["required_recovery_value"] = overall_required_recovery
                else:
                    overall_required_recovery = 0.0
                    evidence["required_recovery_value"] = 0.0

                machine_gb = df_merged.sort_values(by=["Downtime Cost", "Downtime (min)"], ascending=[False, False])
                top_machines = machine_gb.head(2)

                top2_current_loss = 0.0
                total_recovered = 0.0
                total_plant_loss_units = float(df_merged["Downtime (min)"].sum())

                for _, top_row in top_machines.iterrows():
                    machine_id = f"{top_row['Machine ID']} ({top_row['Date']})"
                    raw_machine_id = str(top_row["Machine ID"])
                    m_planned = float(top_row["Planned Time (min)"])
                    m_downtime = float(top_row["Downtime (min)"])
                    m_downtime_cost = float(top_row["Downtime Cost"])
                    error_code = str(top_row.get("Error Code", "Unknown"))
                    
                    top2_current_loss += m_downtime_cost
                    
                    # Proportional Recovery Math
                    if total_plant_loss_units > 0:
                        proportion = m_downtime / total_plant_loss_units
                    else:
                        proportion = 0.0
                        
                    m_rec_down = proportion * overall_required_recovery
                    m_rec_down = min(m_rec_down, m_downtime) # cannot recover more than lost
                    
                    cpm = m_downtime_cost / m_downtime if m_downtime > 0 else 0.0
                    m_est_saving = m_rec_down * cpm
                    
                    total_recovered += m_rec_down
                    
                    contributor = {
                        "machine_id": machine_id,
                        "error_code": error_code,
                        "downtime_contribution": round(m_downtime, 2),
                        "estimated_business_loss": round(m_downtime_cost, 2),
                        "estimated_savings": round(m_est_saving, 2),
                        "projected_loss": round(max(m_downtime_cost - m_est_saving, 0), 2),
                        "recovered_value": round(m_rec_down, 2)
                    }

                    # AI Context
                    if not df_ai.empty:
                        ai_match = df_ai[
                            (df_ai["Machine ID"] == raw_machine_id) & 
                            (df_ai["Date"] == top_row["Date"]) & 
                            (df_ai["Shift"] == top_row["Shift"])
                        ]
                        if not ai_match.empty:
                            contributor["ai_validation"] = str(ai_match.iloc[0].get("AI Validation", "Unknown"))
                            contributor["validation_reason"] = str(ai_match.iloc[0].get("Validation Reason", "None"))
                            contributor["likely_root_cause"] = str(ai_match.iloc[0].get("Likely Root Cause", "Unknown"))
                            contributor["manufacturing_insight"] = str(ai_match.iloc[0].get("Manufacturing Insight", "None"))
                        else:
                            contributor["ai_validation"] = "N/A"
                            contributor["validation_reason"] = "No availability AI context found."
                            contributor["likely_root_cause"] = "Check generic machine profile for general wear and tear issues."
                            contributor["manufacturing_insight"] = "Downtime loss typically points to mechanical or electrical failures."

                    evidence["dominant_contributors"].append(contributor)

                top2_estimated_saving = sum(c["estimated_savings"] for c in evidence["dominant_contributors"])
                evidence["top2_current_loss"] = round(top2_current_loss, 2)
                evidence["top2_estimated_saving"] = round(top2_estimated_saving, 2)
                evidence["top2_projected_loss"] = round(max(top2_current_loss - top2_estimated_saving, 0), 2)
                evidence["top2_recovered_value"] = round(total_recovered, 2)
                    
        except Exception as e:
            print(f"Error in analyze_evidence (Availability): {e}")
            
        return evidence

    def get_business_story(self) -> Dict[str, str]:
        return {
            "objective": "Increase Equipment Uptime",
            "outcome": "Higher Production Hours, Lower Downtime, Better Asset Utilization"
        }

    def get_roadmap(self) -> Dict[str, str]:
        return {
            "Week 1": "Breakdown Analysis",
            "Week 2": "Preventive Maintenance",
            "Week 3": "Spare Parts Optimization",
            "Week 4": "MTTR Improvement"
        }

    def get_recommendation_style(self) -> str:
        return "Only discuss Maintenance, Downtime, Changeovers, Lubrication, MTBF, and MTTR."
        
    def get_risk_assessment(self) -> Dict[str, str]:
        return {
            "Operational Risk": "Low",
            "Implementation Risk": "Medium",
            "Expected Downtime During Rollout": "1 Shift"
        }
        
    def get_priorities(self) -> Dict[str, str]:
        return {
            "Immediate": "Preventive Maintenance",
            "Within 1 Week": "Lubrication",
            "Long Term": "Operator Training"
        }
