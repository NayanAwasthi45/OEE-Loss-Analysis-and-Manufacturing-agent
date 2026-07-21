import os
import logging
from typing import Dict, Any, List, Optional
from .retriever import Retriever
from .prompt_builder import PromptBuilder
from .session_memory import SessionMemory

try:
    import groq
except ImportError:
    groq = None

logger = logging.getLogger(__name__)

class ChatService:
    """
    Main orchestrator for the Manufacturing AI Copilot.
    Handles Recommendations, Ask Anything, and Scenario Simulation.
    """

    def __init__(self, retriever: Retriever, session_memory: SessionMemory, model: str = "llama-3.3-70b-versatile"):
        self.retriever = retriever
        self.session_memory = session_memory
        self.model = model
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY is missing. ChatService will fail to generate answers.")
            self.client = None
        elif groq:
            self.client = groq.Groq(api_key=api_key)
        else:
            self.client = None

    def process_message(self, session_id: str, message: str, mode: str, analytics_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes an incoming chat message based on the selected mode.
        """
        logger.info(f"Processing chat mode='{mode}' for session '{session_id}'")
        
        if mode == "simulation":
            return {
                "reply": "Scenario Simulation is coming in the next phase.",
                "citations": []
            }
            
        if not self.client:
            return {
                "reply": "API Key configuration error. Cannot connect to Groq LLM.",
                "citations": []
            }

        # Determine search query
        search_query = message
        if mode == "recommendation" and analytics_context:
            root_cause = analytics_context.get("AI Root Cause", "")
            machine = analytics_context.get("Machine", "")
            if root_cause:
                search_query = f"{machine} {root_cause} troubleshooting procedures"

        # Retrieve RAG context
        retrieved_docs = self.retriever.retrieve(search_query)

        # Get session history
        chat_history = self.session_memory.get_history(session_id)

        # Build unified prompt
        prompt = PromptBuilder.build_copilot_prompt(
            query=message,
            analytics_context=analytics_context,
            retrieved_docs=retrieved_docs,
            chat_history=chat_history
        )

        # Send as system or user based on mode? The unified prompt is practically a system + user prompt combined.
        # We'll just send it as a user message to keep it simple, since history is baked into the prompt text itself.
        messages = [{"role": "user", "content": prompt}]
        
        # Save user message to memory (only for Ask Anything to avoid saving raw system commands)
        if mode == "ask_anything":
            self.session_memory.add_message(session_id, "user", message)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            reply_text = response.choices[0].message.content.strip()
            
            if mode != "recommendation":
                self.session_memory.add_message(session_id, "assistant", reply_text)
                
            # Extract unique citations
            citations = []
            for doc in retrieved_docs:
                source = doc["metadata"].get("source")
                if source and source not in citations:
                    citations.append(source)
                    
            return {
                "reply": reply_text,
                "citations": citations
            }
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            return {
                "reply": f"Sorry, I encountered an error generating the response: {str(e)}",
                "citations": []
            }
