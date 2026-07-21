from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseScenarioPlugin(ABC):
    """
    Abstract Base Class for Scenario Plugins.
    Defines the contract for providing scenario-specific business logic,
    roadmaps, risk assessments, and stories to the Context Builder.
    """
    
    @property
    @abstractmethod
    def scenario_name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def primary_goal(self) -> str:
        pass

    @property
    @abstractmethod
    def root_problem(self) -> str:
        pass

    @abstractmethod
    def get_focus_areas(self) -> List[str]:
        pass

    @abstractmethod
    def get_business_story(self) -> Dict[str, str]:
        """Returns Business Objective and Expected Outcome."""
        pass

    @abstractmethod
    def get_roadmap(self) -> Dict[str, str]:
        """Returns Week 1 to Week N roadmap."""
        pass

    @abstractmethod
    def get_recommendation_style(self) -> str:
        """Instruction for LLM on what to discuss exclusively."""
        pass
        
    @abstractmethod
    def get_risk_assessment(self) -> Dict[str, str]:
        """Returns Operational Risk, Implementation Risk, Expected Downtime."""
        pass
        
    @abstractmethod
    def get_priorities(self) -> Dict[str, str]:
        """Returns Immediate, Within 1 Week, and Long Term priorities."""
        pass
        
    def calculate_roi(self, savings: float, investment: str) -> str:
        """Generic calculation for ROI based on deterministic savings."""
        if savings <= 0:
            return "None"
        if investment == "Low" and savings > 5000:
            return "High"
        elif investment == "Medium" and savings > 15000:
            return "High"
        elif investment == "High":
            return "Low" if savings < 20000 else "Medium"
        return "Medium"
        
    def calculate_confidence(self, projected_oee: float) -> str:
        if projected_oee > 100:
            return "0%"
        if projected_oee > 95:
            return "85%"
        return "96%"
