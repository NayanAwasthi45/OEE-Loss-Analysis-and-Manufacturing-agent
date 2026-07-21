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
