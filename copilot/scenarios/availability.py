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
