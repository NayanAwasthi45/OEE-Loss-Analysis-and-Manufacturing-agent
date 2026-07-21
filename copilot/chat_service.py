import os
import logging
from typing import Dict, Any, Optional
import json
from copilot.memory import SessionMemory
from .scenario_service import ScenarioService

from rag.retriever import Retriever
from rag.prompt_builder import PromptBuilder
from copilot.scenario_context_builder import ScenarioContextBuilder
try:
    import groq
except ImportError:
    groq = None

logger = logging.getLogger(__name__)

class CopilotChatService:
    """
    Enterprise Copilot Orchestrator.
    Strictly routes requests to 4 distinct modes: general_chat, manufacturing_question, recommendation, simulation.
    """

    def __init__(self, retriever: Retriever, session_memory: SessionMemory, model: str = "llama-3.3-70b-versatile"):
        self.retriever = retriever
        self.session_memory = session_memory
        self.model = model
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY is missing. Copilot will fail to generate answers.")
            self.client = None
        elif groq:
            self.client = groq.Groq(api_key=api_key)
        else:
            self.client = None

        self.scenario_service = ScenarioService()
        self.scenario_context_builder = ScenarioContextBuilder()

    def process_message(self, session_id: str, message: str, mode: str, analytics_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point for Copilot messages.
        `mode` is explicitly provided by the UI. No automatic routing.
        """
        if not self.client:
            return {"reply": "API Key configuration error. Cannot connect to Groq LLM.", "citations": []}

        # Validate mode
        valid_modes = ["general_chat", "manufacturing_question", "recommendation", "simulation"]
        # Treat 'ask_anything' from older UI state as 'general_chat' if it sneaks through, though UI is updated
        if mode == "ask_anything":
            mode = "general_chat"
            
        is_simulation = mode == "simulation" or mode.startswith("simulate:")
        
        if mode not in valid_modes and not is_simulation:
            return {"reply": "Invalid mode selected. Please select a valid module.", "citations": []}
            
        logger.info(f"Routed message to strict mode: {mode}")

        # Isolate session memory by mode
        actual_mode = "simulation" if is_simulation else mode
        mode_session_id = f"{session_id}_{actual_mode}"

        # 2. Handle Scenario Simulation
        # Mode arrives as "simulate:availability:10" or "simulate:compare_all:10:5:4"
        if actual_mode == "simulation":
            scenario_type = "availability"
            improvement_pct = 10.0
            comp_pcts = None
            
            if mode.startswith("simulate:"):
                parts = mode.split(":")
                if len(parts) >= 2:
                    scenario_type = parts[1].strip().lower()
                if scenario_type == "compare_all" and len(parts) >= 5:
                    comp_pcts = {
                        "availability": float(parts[2]),
                        "performance": float(parts[3]),
                        "quality": float(parts[4])
                    }
                elif len(parts) >= 3:
                    try:
                        improvement_pct = float(parts[2])
                    except ValueError:
                        improvement_pct = 10.0
                        
            if improvement_pct <= 0:
                improvement_pct = 5.0  # Prevent 0% math generating identical baselines
                        
            if scenario_type not in ["availability", "performance", "quality", "compare_all"]:
                scenario_type = "availability"
                
            logger.info("--------------------------------------------------")
            logger.info(f"Scenario requested:")
            logger.info(f"KPI: {scenario_type.capitalize()}")
            if comp_pcts:
                logger.info(f"Improvement: A(+{comp_pcts['availability']}%) P(+{comp_pcts['performance']}%) Q(+{comp_pcts['quality']}%)")
            else:
                logger.info(f"Improvement: +{improvement_pct}%")
            logger.info(f"Running {scenario_type.capitalize()} simulation...")
            
            # Deterministic math calculation
            simulation_json = self.scenario_service.simulate(scenario_type, improvement_pct, analytics_context or {}, comp_pcts=comp_pcts)
            
            if "error" in simulation_json:
                error_msg = simulation_json["error"]
                self.session_memory.add_message(mode_session_id, "user", f"Run scenario simulation for {scenario_type} (+{improvement_pct}%)")
                self.session_memory.add_message(mode_session_id, "assistant", error_msg)
                return {"reply": error_msg, "citations": []}
                
            # Build Context Using the new Plugin Architecture
            enriched_context = self.scenario_context_builder.build_context(scenario_type, simulation_json)
                
            # LLM Generation for explanation and formatting
            prompt = PromptBuilder.build_simulation_prompt(scenario_type, improvement_pct, enriched_context, analytics_context or {})
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1500
                )
                reply_text = response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Groq API error during simulation: {e}")
                reply_text = f"Simulation math succeeded, but LLM failed to generate explanation. Raw Data:\n{json.dumps(simulation_json, indent=2)}"
                
            logger.info(f"Simulation completed successfully.")
            logger.info("--------------------------------------------------")
            self.session_memory.add_message(mode_session_id, "user", f"Ran scenario simulation for {scenario_type} (+{improvement_pct}%)")
            self.session_memory.add_message(mode_session_id, "assistant", reply_text)
            return {"reply": reply_text, "citations": []}

        chat_history = self.session_memory.get_history(mode_session_id)
        retrieved_docs = []
        citations = []

        # 3. Mode Routing
        if mode == "general_chat":
            prompt = PromptBuilder.build_general_prompt(message, chat_history)
        
        elif mode == "manufacturing_question":
            retrieved_docs = self.retriever.retrieve(message)
            prompt = PromptBuilder.build_manufacturing_prompt(message, retrieved_docs, chat_history)
            
        elif mode == "recommendation":
            search_query = message
            if analytics_context:
                root_cause = analytics_context.get("AI Root Cause", "")
                machine = analytics_context.get("Machine", "")
                if root_cause:
                    search_query = f"{machine} {root_cause} troubleshooting procedures"
            
            retrieved_docs = self.retriever.retrieve(search_query)
            prompt = PromptBuilder.build_recommendation_prompt(
                query=message,
                analytics_context=analytics_context,
                retrieved_docs=retrieved_docs,
                chat_history=chat_history
            )

        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            reply_text = response.choices[0].message.content.strip()
            
            self.session_memory.add_message(mode_session_id, "user", message)
            self.session_memory.add_message(mode_session_id, "assistant", reply_text)
                
            citations = []
            for doc in retrieved_docs:
                source = doc["metadata"].get("source")
                if source and source not in citations:
                    citations.append(source)
                    
            return {"reply": reply_text, "citations": citations}
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            return {"reply": f"Error: {str(e)}", "citations": []}
