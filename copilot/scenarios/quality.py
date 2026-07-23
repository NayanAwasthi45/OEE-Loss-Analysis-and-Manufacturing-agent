from typing import Dict, Any, List
from .base_scenario import BaseScenarioPlugin

class QualityScenario(BaseScenarioPlugin):
    @property
    def scenario_name(self) -> str:
        return "Quality"
        
    @property
    def primary_goal(self) -> str:
        return "Reduce defects."

    @property
    def root_problem(self) -> str:
        return "Scrap and Rework."

    def get_focus_areas(self) -> List[str]:
        return [
            "Inspection",
            "Calibration",
            "Root Cause Analysis",
            "Process Capability",
            "Quality Audits",
            "Operator Quality Training"
        ]

    def analyze_evidence(self, simulation_math: Dict[str, Any]) -> Dict[str, Any]:
        import pandas as pd
        import os
        
        evidence = {
            "required_recovery_metric": "Defective Parts",
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
            if "scenarios" in simulation_math and "Quality" in simulation_math["scenarios"]:
                applied_pct = simulation_math["scenarios"]["Quality"].get("applied_pct", 5.0)
                req_recovery = simulation_math.get("Projected Quality", 0) - simulation_math.get("current", {}).get("Quality", 0)
                # Convert to units
                if req_recovery > 0:
                    evidence["required_recovery"] = "Reduce Defects by " + str(round(req_recovery, 2)) + "%"
                    evidence["required_recovery_value"] = round(req_recovery * 10, 1) # approximation
                    req_recovery = evidence["required_recovery_value"]
                else:
                    evidence["required_recovery"] = "Maintain Quality"
                    evidence["required_recovery_value"] = 0
                    req_recovery = 0
                    
                if not df_val.empty and "Defective Parts" in df_val.columns:
                    # Filter only quality loss codes
                    df_val_qual = df_val[df_val["Error Code"].astype(str).str.startswith("DEF-")]
                    machine_gb = df_val_qual.groupby("Machine ID")["Defective Parts"].sum().reset_index()
                    machine_gb = machine_gb.sort_values(by="Defective Parts", ascending=False)
                    
                    # Take top 2 machines
                    top_machines = machine_gb.head(2)
                    remaining_recovery = req_recovery
                    
                    for _, top_row in top_machines.iterrows():
                        machine_id = str(top_row["Machine ID"])
                        
                        # Find the dominant Error Code for this specific machine
                        machine_df = df_val_qual[df_val_qual["Machine ID"] == machine_id]
                        error_gb = machine_df.groupby("Error Code")["Defective Parts"].sum().reset_index()
                        error_gb = error_gb.sort_values(by="Defective Parts", ascending=False)
                        
                        if not error_gb.empty:
                            error_code = str(error_gb.iloc[0]["Error Code"])
                            error_contribution = round(float(error_gb.iloc[0]["Defective Parts"]), 2)
                        else:
                            error_code = "Unknown"
                            error_contribution = round(float(top_row["Defective Parts"]), 2)
                        
                        contributor = {
                            "machine_id": machine_id,
                            "error_code": error_code,
                            "defects_contribution": error_contribution,
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
                            ai_match = df_ai[(df_ai["Machine ID"] == machine_id) & (df_ai["Dominant Loss"] == "Quality")]
                            if not ai_match.empty:
                                contributor["ai_validation"] = str(ai_match.iloc[0].get("AI Validation", "Unknown"))
                                contributor["validation_reason"] = str(ai_match.iloc[0].get("Validation Reason", "None"))
                                contributor["likely_root_cause"] = str(ai_match.iloc[0].get("Likely Root Cause", "Unknown"))
                                contributor["manufacturing_insight"] = str(ai_match.iloc[0].get("Manufacturing Insight", "None"))
                            else:
                                contributor["ai_validation"] = "N/A"
                                contributor["validation_reason"] = "No quality-specific AI analysis available."
                                contributor["likely_root_cause"] = "Defects due to calibration issues, tool wear, or incorrect machine parameters."
                                contributor["manufacturing_insight"] = "Quality loss typically points to process capability issues. Refer to generic machine profile knowledge."
                        
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
                                if "Scrap Cost" in biz_match.columns:
                                    hist_loss = round(float(biz_match["Scrap Cost"].sum()), 2)
                                else:
                                    hist_loss = round(float(biz_match["Estimated Business Loss"].sum()), 2)
                                contributor["estimated_business_loss"] = hist_loss
                                contributor["primary_business_driver"] = str(biz_match.iloc[0].get("Primary Business Driver", "Unknown"))
                                contributor["priority"] = str(biz_match.iloc[0].get("Priority", "Low"))
                                
                        # Calculate Savings per machine
                        rate = 0
                        if contributor["defects_contribution"] > 0:
                            rate = contributor["estimated_business_loss"] / contributor["defects_contribution"]
                        
                        recoverable = min(remaining_recovery, contributor["defects_contribution"])
                        machine_savings = recoverable * rate
                        contributor["estimated_savings"] = round(machine_savings, 2)
                        contributor["projected_loss"] = round(contributor["estimated_business_loss"] - machine_savings, 2)
                        
                        remaining_recovery -= recoverable
                        if remaining_recovery < 0:
                            remaining_recovery = 0
                                
                        evidence["dominant_contributors"].append(contributor)
                    
        except Exception as e:
            print(f"Error in analyze_evidence (Quality): {e}")
            
        return evidence

    def get_business_story(self) -> Dict[str, str]:
        return {
            "objective": "Reduce Manufacturing Defects",
            "outcome": "Lower Scrap, Lower Rework, Higher Customer Satisfaction"
        }

    def get_roadmap(self) -> Dict[str, str]:
        return {
            "Week 1": "Defect Analysis",
            "Week 2": "Calibration",
            "Week 3": "Inspection Improvements",
            "Week 4": "Process Capability Review"
        }

    def get_recommendation_style(self) -> str:
        return "Only discuss Scrap, Rework, Inspection, Calibration, First Pass Yield, and Defects. Never recommend calibration inside Availability unless dashboard evidence supports it. Never recommend preventive maintenance as the primary recommendation inside Quality unless downtime is also a major issue."
        
    def get_risk_assessment(self) -> Dict[str, str]:
        return {
            "Operational Risk": "Low",
            "Implementation Risk": "High",
            "Expected Downtime During Rollout": "0.5 Shifts"
        }
        
    def get_priorities(self) -> Dict[str, str]:
        return {
            "Immediate": "Defect Analysis",
            "Within 1 Week": "Calibration",
            "Long Term": "Process Capability"
        }
