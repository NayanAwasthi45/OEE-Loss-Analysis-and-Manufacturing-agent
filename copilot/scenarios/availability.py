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
            
            # 1. Required Recovery Calculation
            applied_pct = 5.0
            if "scenarios" in simulation_math and "Availability" in simulation_math["scenarios"]:
                applied_pct = simulation_math["scenarios"]["Availability"].get("applied_pct", 5.0)
            elif "improvement_pct" in simulation_math:
                applied_pct = simulation_math.get("improvement_pct", 5.0)
                
            if "Planned Time (min)" in df_val.columns and "Downtime (min)" in df_val.columns:
                    total_planned = df_val["Planned Time (min)"].sum()
                    total_downtime = df_val["Downtime (min)"].sum()
                    
                    if total_planned > 0:
                        current_avail_pct = ((total_planned - total_downtime) / total_planned) * 100
                        target_avail_pct = current_avail_pct + applied_pct
                        
                        new_downtime = total_planned - (target_avail_pct / 100.0 * total_planned)
                        required_recovery = total_downtime - new_downtime
                        evidence["required_recovery_value"] = round(max(0, required_recovery), 2)
            
            # 2. Pareto Analysis on Downtime (min) grouped by Machine ID
            df_val_dt = df_val[df_val["Downtime (min)"] > 0]
            if not df_val_dt.empty and "Machine ID" in df_val_dt.columns and "Error Code" in df_val_dt.columns:
                # Filter to only downtime error codes to avoid cross-pollination
                df_val_dt = df_val_dt[df_val_dt["Error Code"].astype(str).str.startswith("DT-")]
                
                if not df_val_dt.empty:
                    # Group by Machine ID first to get overall machine contribution
                    machine_gb = df_val_dt.groupby("Machine ID")["Downtime (min)"].sum().reset_index()
                    machine_gb = machine_gb.sort_values(by="Downtime (min)", ascending=False)
                    
                    # Take top 2 machines
                    top_machines = machine_gb.head(2)
                    remaining_recovery = evidence.get("required_recovery_value", 0)
                    
                    for _, top_row in top_machines.iterrows():
                        machine_id = str(top_row["Machine ID"])
                        
                        # Find the dominant Error Code for this specific machine
                        machine_df = df_val_dt[df_val_dt["Machine ID"] == machine_id]
                        error_gb = machine_df.groupby("Error Code")["Downtime (min)"].sum().reset_index()
                        error_gb = error_gb.sort_values(by="Downtime (min)", ascending=False)
                        
                        if not error_gb.empty:
                            error_code = str(error_gb.iloc[0]["Error Code"])
                            error_contribution = round(float(error_gb.iloc[0]["Downtime (min)"]), 2)
                        else:
                            error_code = "Unknown"
                            error_contribution = round(float(top_row["Downtime (min)"]), 2)
                        
                        contributor = {
                            "machine_id": machine_id,
                            "error_code": error_code,
                            "downtime_contribution": error_contribution,
                            "ai_validation": "Unknown",
                            "validation_reason": "None",
                            "likely_root_cause": "Unknown",
                            "manufacturing_insight": "None",
                            "estimated_business_loss": 0.0,
                            "primary_business_driver": "Unknown",
                            "priority": "Low"
                        }
                        
                        # 3. AI Validation
                        if not df_ai.empty and "Machine ID" in df_ai.columns and "Dominant Loss" in df_ai.columns:
                            ai_match = df_ai[(df_ai["Machine ID"] == machine_id) & (df_ai["Error Code"] == error_code) & (df_ai["Dominant Loss"] == "Availability")]
                            if not ai_match.empty:
                                contributor["ai_validation"] = str(ai_match.iloc[0].get("AI Validation", "Unknown"))
                                contributor["validation_reason"] = str(ai_match.iloc[0].get("Validation Reason", "None"))
                                contributor["likely_root_cause"] = str(ai_match.iloc[0].get("Likely Root Cause", "Unknown"))
                                contributor["manufacturing_insight"] = str(ai_match.iloc[0].get("Manufacturing Insight", "None"))
                            else:
                                contributor["ai_validation"] = "N/A"
                                contributor["validation_reason"] = "No availability-specific AI analysis available for this error code."
                                contributor["likely_root_cause"] = "Mechanical or electrical failure."
                                contributor["manufacturing_insight"] = "Availability loss typically points to unplanned downtime. Refer to generic machine profile knowledge."
                        
                        # 4. Business Impact
                        contributor["estimated_business_loss"] = 0.0
                        contributor["estimated_savings"] = 0.0
                        contributor["projected_loss"] = 0.0
                        if not df_biz.empty and not df_val.empty and "Machine ID" in df_biz.columns and "Machine ID" in df_val.columns:
                            try:
                                df_merged = pd.merge(df_biz, df_val, on=["Machine ID", "Date", "Shift"])
                                biz_match = df_merged[(df_merged["Machine ID"] == machine_id) & (df_merged["Error Code"] == error_code)]
                            except KeyError:
                                biz_match = df_biz[df_biz["Machine ID"] == machine_id] # fallback if merge fails

                            if not biz_match.empty:
                                if "Downtime Cost" in biz_match.columns:
                                    hist_loss = round(float(biz_match["Downtime Cost"].sum()), 2)
                                else:
                                    hist_loss = round(float(biz_match["Estimated Business Loss"].sum()), 2)
                                contributor["estimated_business_loss"] = hist_loss
                                contributor["primary_business_driver"] = str(biz_match.iloc[0].get("Primary Business Driver", "Unknown"))
                                contributor["priority"] = str(biz_match.iloc[0].get("Priority", "Low"))
                                
                        # Calculate Savings per machine
                        rate = 0
                        if contributor["downtime_contribution"] > 0:
                            rate = contributor["estimated_business_loss"] / contributor["downtime_contribution"]
                        
                        recoverable = min(remaining_recovery, contributor["downtime_contribution"])
                        machine_savings = recoverable * rate
                        contributor["estimated_savings"] = round(machine_savings, 2)
                        contributor["projected_loss"] = round(contributor["estimated_business_loss"] - machine_savings, 2)
                        
                        remaining_recovery -= recoverable
                        if remaining_recovery < 0:
                            remaining_recovery = 0
                                
                        evidence["dominant_contributors"].append(contributor)
                    
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
