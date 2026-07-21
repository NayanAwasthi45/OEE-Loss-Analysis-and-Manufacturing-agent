import logging
try:
    import groq
except ImportError:
    groq = None

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Classifies incoming user messages into specific copilot skills.
    Possible intents:
    - greeting
    - manufacturing_question
    - recommendation
    - simulation (though simulation is usually triggered by a direct button, user might type it)
    - general_chat
    """

    def __init__(self, client):
        self.client = client
        self.model = "llama-3.3-70b-versatile"

    def classify(self, message: str) -> str:
        """Returns the intent string."""
        if not self.client:
            return "manufacturing_question" # fallback

        # Simple heuristic overrides for speed
        msg_lower = message.lower().strip()
        if msg_lower in ["hi", "hello", "hey", "good morning", "good afternoon"]:
            return "greeting"
        
        if "simulate" in msg_lower or "scenario" in msg_lower:
            return "simulation"
            
        if "recommend" in msg_lower or "what should i do" in msg_lower or "improve" in msg_lower:
            return "recommendation"

        prompt = f"""Classify the user's message into EXACTLY ONE of the following intents. Output ONLY the intent name in lowercase, nothing else.

INTENTS:
1. greeting: Simple greetings or questions about the bot itself (e.g., "Hi", "Who are you?").
2. recommendation: Asking for advice, improvements, or recommendations based on current data (e.g., "How can I improve OEE?", "What should I do?").
3. simulation: Asking to simulate a scenario or predict improvements.
4. manufacturing_question: Asking for factual manufacturing knowledge, definitions, or how to perform a task (e.g., "What is OEE?", "How to replace a bearing?").
5. general_chat: Anything else.

USER MESSAGE: {message}

INTENT:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10
            )
            intent = response.choices[0].message.content.strip().lower()
            
            valid_intents = ["greeting", "recommendation", "simulation", "manufacturing_question", "general_chat"]
            if intent in valid_intents:
                return intent
            return "manufacturing_question"
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return "manufacturing_question" # fallback
