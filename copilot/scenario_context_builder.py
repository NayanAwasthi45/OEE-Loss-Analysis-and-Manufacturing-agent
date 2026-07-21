from typing import Dict, Any, Optional
from .scenarios.availability import AvailabilityScenario
from .scenarios.performance import PerformanceScenario
from .scenarios.quality import QualityScenario
from .scenarios.base_scenario import BaseScenarioPlugin

class ScenarioContextBuilder:
    """
    Acts as the Scenario Engine. Merges deterministic math from ScenarioService
    with rich business metrics and roadmaps from the Scenario Plugins.
    """
    
    def __init__(self):
        self.plugins = {
            "availability": AvailabilityScenario(),
            "performance": PerformanceScenario(),
            "quality": QualityScenario()
        }
        
    def get_plugin(self, scenario_type: str) -> Optional[BaseScenarioPlugin]:
        return self.plugins.get(scenario_type.lower())

    def build_context(self, scenario_type: str, simulation_math: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the unified business context to feed the LLM.
        """
        if scenario_type == "compare_all":
            return self._build_compare_all_context(simulation_math)
            
        plugin = self.get_plugin(scenario_type)
        if not plugin:
            return simulation_math # Fallback if plugin doesn't exist
            
        savings = simulation_math.get("Savings", 0.0)
        proj_oee = simulation_math.get("Projected OEE", 0.0)
        
        # Merge plugin data into the math context
        context = {
            "deterministic_math": simulation_math,
            "business_story": plugin.get_business_story(),
            "root_problem": plugin.root_problem,
            "focus_areas": plugin.get_focus_areas(),
            "roadmap": plugin.get_roadmap(),
            "risk_assessment": plugin.get_risk_assessment(),
            "priorities": plugin.get_priorities(),
            "roi": plugin.calculate_roi(savings, plugin.get_risk_assessment()["Implementation Risk"]),
            "confidence": plugin.calculate_confidence(proj_oee),
            "recommendation_style": plugin.get_recommendation_style()
        }
        return context

    def _build_compare_all_context(self, simulation_math: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the context for Compare All. 
        It evaluates all 3 plugins to assign ROI and Confidence for each ranking.
        """
        enriched_scenarios = {}
        scenarios_math = simulation_math.get("scenarios", {})
        
        for stype, smath in scenarios_math.items():
            plugin = self.get_plugin(stype)
            if plugin:
                savings = smath.get("Savings", 0.0)
                proj_oee = smath.get("Projected OEE", 0.0)
                risk = plugin.get_risk_assessment()["Implementation Risk"]
                
                smath["roi"] = plugin.calculate_roi(savings, risk)
                smath["confidence"] = plugin.calculate_confidence(proj_oee)
                smath["implementation_difficulty"] = risk
                smath["priorities"] = plugin.get_priorities()
            
            enriched_scenarios[stype] = smath
            
        return {
            "deterministic_math": {
                "current": simulation_math.get("current"),
                "best_scenario": simulation_math.get("best_scenario"),
                "scenarios": enriched_scenarios
            },
            "compare_all_rules": "Rank the scenarios by Savings and ROI. Explain why the best scenario won based on these enriched metrics."
        }
