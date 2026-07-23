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
            
            # 1. Required Recovery Calculation
            req_recovery = simulation_math.get("Projected Performance", 0) - simulation_math.get("current", {}).get("Performance", 0)
            # Convert to units using some basic math (approximation if needed)
            if req_recovery > 0:
                evidence["required_recovery"] = "Increase Performance by " + str(round(req_recovery, 2)) + "%"
                evidence["required_recovery_value"] = round(req_recovery * 10, 1) # simple unit conversion approximation
                req_recovery = evidence["required_recovery_value"]
            else:
                evidence["required_recovery"] = "Maintain Performance"
                evidence["required_recovery_value"] = 0
                req_recovery = 0
                
            if not df_val.empty and "Production Loss (units)" in df_val.columns:
                # Filter only performance loss codes
                df_val_perf = df_val[(~df_val["Error Code"].astype(str).str.startswith("DT-")) & (~df_val["Error Code"].astype(str).str.startswith("DEF-"))]
                machine_gb = df_val_perf.groupby("Machine ID")["Production Loss (units)"].sum().reset_index()
                machine_gb = machine_gb.sort_values(by="Production Loss (units)", ascending=False)
                
                # Take top 2 machines
                top_machines = machine_gb.head(2)
                remaining_recovery = req_recovery
                
                for _, top_row in top_machines.iterrows():
                    machine_id = str(top_row["Machine ID"])
                    
                    # Get error code from validated data, but exclude Downtime codes
                    error_contribution = round(float(top_row["Production Loss (units)"]), 2)
                    error_code_val = "N/A (Speed Loss)"
                    
                    if not df_val.empty and "Machine ID" in df_val.columns and "Error Code" in df_val.columns:
                        val_match = df_val[(df_val["Machine ID"] == machine_id) & (~df_val["Error Code"].astype(str).str.startswith("DT-")) & (~df_val["Error Code"].astype(str).str.startswith("DEF-"))]
                        if not val_match.empty and not pd.isna(val_match.iloc[0].get("Error Code")):
                            # get the most frequent non-DT/DEF error code for this machine
                            error_gb = val_match.groupby("Error Code")["Production Loss (units)"].sum().reset_index()
                            error_gb = error_gb.sort_values(by="Production Loss (units)", ascending=False)
                            if not error_gb.empty:
                                error_code_val = str(error_gb.iloc[0]["Error Code"])
                                error_contribution = round(float(error_gb.iloc[0]["Production Loss (units)"]), 2)
                                
                    contributor = {
                        "machine_id": machine_id,
                        "error_code": error_code_val,
                        "production_loss_contribution": error_contribution,
                        "ai_validation": "Unknown",
                    }
                    
                    # 3. AI Validation
                    if not df_ai.empty and "Machine ID" in df_ai.columns and "Dominant Loss" in df_ai.columns:
                        ai_match = df_ai[(df_ai["Machine ID"] == machine_id) & (df_ai["Dominant Loss"] == "Performance")]
                        if not ai_match.empty:
                            contributor["ai_validation"] = str(ai_match.iloc[0].get("AI Validation", "Unknown"))
                            contributor["validation_reason"] = str(ai_match.iloc[0].get("Validation Reason", "None"))
                            contributor["likely_root_cause"] = str(ai_match.iloc[0].get("Likely Root Cause", "Unknown"))
                            contributor["manufacturing_insight"] = str(ai_match.iloc[0].get("Manufacturing Insight", "None"))
                        else:
                            contributor["ai_validation"] = "N/A"
                            contributor["validation_reason"] = "No performance-specific AI analysis available."
                            contributor["likely_root_cause"] = "Speed loss due to minor stops, operator inefficiency, or suboptimal machine settings."
                            contributor["manufacturing_insight"] = "Performance loss typically points to cycle time deviations. Refer to generic machine profile knowledge."
                    
                    # 4. Business Impact
                    contributor["estimated_business_loss"] = 0.0
                    contributor["estimated_savings"] = 0.0
                    contributor["projected_loss"] = 0.0
                    if not df_biz.empty and not df_val.empty and "Machine ID" in df_biz.columns and "Machine ID" in df_val.columns:
                        try:
                            df_merged = pd.merge(df_biz, df_val, on=["Machine ID", "Date", "Shift"])
                            biz_match = df_merged[(df_merged["Machine ID"] == machine_id) & (df_merged["Error Code"] == error_code_val)]
                        except KeyError:
                            biz_match = df_biz[df_biz["Machine ID"] == machine_id] # fallback if merge fails

                        if not biz_match.empty:
                            if "Production Loss Cost" in biz_match.columns:
                                hist_loss = round(float(biz_match["Production Loss Cost"].sum()), 2)
                            else:
                                hist_loss = round(float(biz_match["Estimated Business Loss"].sum()), 2)
                            contributor["estimated_business_loss"] = hist_loss
                            contributor["primary_business_driver"] = str(biz_match.iloc[0].get("Primary Business Driver", "Unknown"))
                            contributor["priority"] = str(biz_match.iloc[0].get("Priority", "Low"))
                            
                    # Calculate Savings per machine
                    rate = 0
                    if contributor["production_loss_contribution"] > 0:
                        rate = contributor["estimated_business_loss"] / contributor["production_loss_contribution"]
                    
                    recoverable = min(remaining_recovery, contributor["production_loss_contribution"])
                    machine_savings = recoverable * rate
                    contributor["estimated_savings"] = round(machine_savings, 2)
                    contributor["projected_loss"] = round(contributor["estimated_business_loss"] - machine_savings, 2)
                    
                    remaining_recovery -= recoverable
                    if remaining_recovery < 0:
                        remaining_recovery = 0
                            
                    evidence["dominant_contributors"].append(contributor)
                    
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
