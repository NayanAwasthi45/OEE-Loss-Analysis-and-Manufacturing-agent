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
            
            applied_pct = 5.0
            if "scenarios" in simulation_math and "Quality" in simulation_math["scenarios"]:
                applied_pct = simulation_math["scenarios"]["Quality"].get("applied_pct", 5.0)
            elif "improvement_pct" in simulation_math:
                applied_pct = simulation_math.get("improvement_pct", 5.0)

            if not df_val.empty and not df_biz.empty:
                df_merged = pd.merge(df_val, df_biz, on=["Machine ID", "Date", "Shift"])
                
                # 1. Required Recovery Calculation
                if "Total Parts Produced" in df_val.columns:
                    total_parts = float(df_val["Total Parts Produced"].sum())
                    overall_required_recovery = round(total_parts * (applied_pct / 100.0), 2)
                    evidence["required_recovery_value"] = overall_required_recovery
                else:
                    overall_required_recovery = 0.0
                    evidence["required_recovery_value"] = 0.0

                machine_gb = df_merged.sort_values(by=["Scrap Cost", "Defective Parts"], ascending=[False, False])
                top_machines = machine_gb.head(2)

                top2_current_loss = 0.0
                total_recovered = 0.0
                total_plant_loss_units = float(df_merged["Defective Parts"].sum())

                for _, top_row in top_machines.iterrows():
                    machine_id = f"{top_row['Machine ID']} ({top_row['Date']})"
                    raw_machine_id = str(top_row["Machine ID"])
                    m_total_parts = float(top_row["Total Parts Produced"])
                    m_defective = float(top_row["Defective Parts"])
                    m_scrap_cost = float(top_row["Scrap Cost"])
                    error_code = str(top_row.get("Error Code", "N/A (General Quality Loss)"))
                    
                    top2_current_loss += m_scrap_cost
                    
                    # Proportional Recovery Math
                    if total_plant_loss_units > 0:
                        proportion = m_defective / total_plant_loss_units
                    else:
                        proportion = 0.0
                        
                    m_rec_defects = proportion * overall_required_recovery
                    m_rec_defects = min(m_rec_defects, m_defective) # cannot recover more than lost
                    
                    cpd = m_scrap_cost / m_defective if m_defective > 0 else 0.0
                    m_est_saving = m_rec_defects * cpd
                    
                    total_recovered += m_rec_defects
                    
                    contributor = {
                        "machine_id": machine_id,
                        "error_code": error_code,
                        "quality_loss_contribution": round(m_defective, 2),
                        "estimated_business_loss": round(m_scrap_cost, 2),
                        "estimated_savings": round(m_est_saving, 2),
                        "projected_loss": round(max(m_scrap_cost - m_est_saving, 0), 2),
                        "recovered_value": round(m_rec_defects, 2)
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
                            contributor["validation_reason"] = "No quality AI context found."
                            contributor["likely_root_cause"] = "Check generic machine profile for calibration or material issues."
                            contributor["manufacturing_insight"] = "Scrap loss points to precision or material defects."

                    evidence["dominant_contributors"].append(contributor)

                top2_estimated_saving = sum(c["estimated_savings"] for c in evidence["dominant_contributors"])
                evidence["top2_current_loss"] = round(top2_current_loss, 2)
                evidence["top2_estimated_saving"] = round(top2_estimated_saving, 2)
                evidence["top2_projected_loss"] = round(max(top2_current_loss - top2_estimated_saving, 0), 2)
                evidence["top2_recovered_value"] = round(total_recovered, 2)
                    
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
