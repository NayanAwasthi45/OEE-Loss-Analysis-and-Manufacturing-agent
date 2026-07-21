import os
import logging
from typing import Dict, Any, Optional
from copilot.memory import SessionMemory
from .scenario_service import ScenarioService

from rag.retriever import Retriever
from rag.prompt_builder import PromptBuilder
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
        if "simulate:" in mode:
            mode = "simulation"
        
        if mode not in valid_modes and mode != "simulation":
            return {"reply": "Invalid mode selected. Please select a valid module.", "citations": []}
            
        logger.info(f"Routed message to strict mode: {mode}")

        # Isolate session memory by mode
        # If mode was 'simulate:availability', it's still mapped to 'simulation' intent contextually.
        actual_mode = "simulation" if mode.startswith("simulate:") else mode
        mode_session_id = f"{session_id}_{actual_mode}"

        # 2. Handle Scenario Simulation (Deterministic, No RAG, No LLM generation needed)
        # Note: In the UI, the mode is "simulate:availability"
        if actual_mode == "simulation":
            scenario_type = str(mode).replace("simulate:", "").strip().lower()
            if scenario_type not in ["availability", "performance", "quality"]:
                scenario_type = "availability"
                
            reply = self.scenario_service.simulate(scenario_type, analytics_context or {})
            self.session_memory.add_message(mode_session_id, "user", f"Ran scenario simulation for {scenario_type}")
            self.session_memory.add_message(mode_session_id, "assistant", reply)
            return {"reply": reply, "citations": []}

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
