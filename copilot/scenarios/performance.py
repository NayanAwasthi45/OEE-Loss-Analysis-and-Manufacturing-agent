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
