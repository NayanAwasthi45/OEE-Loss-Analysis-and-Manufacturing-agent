from typing import Dict, List

class SessionMemory:
    """
    Lightweight in-memory storage for chat histories.
    Maintains conversation context per session.
    """

    def __init__(self, max_history: int = 10):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_history = max_history

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Returns the chat history for a session."""
        return self.sessions.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        """Adds a message to the session history."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            
        self.sessions[session_id].append({"role": role, "content": content})
        
        # Truncate to max history to prevent context overflow
        if len(self.sessions[session_id]) > self.max_history:
            # Keep the most recent messages
            self.sessions[session_id] = self.sessions[session_id][-self.max_history:]
            
    def clear_session(self, session_id: str):
        """Clears a session's history."""
        if session_id in self.sessions:
            del self.sessions[session_id]
