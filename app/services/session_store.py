import uuid
from typing import Dict, Any, List, Optional

# Global in-memory storage
# Structure: { "session_id": { "cv": {}, "job": "", "current_state": "", "chat_history": [], ... } }
SESSIONS: Dict[str, Any] = {}

class SessionManager:
    @staticmethod
    def create_session(cv_data: dict, job_position: str, mode: str) -> str:
        """
        Initialize a new session with default state.
        """
        session_id = str(uuid.uuid4())
        
        SESSIONS[session_id] = {
            "cv": cv_data,
            "job": job_position,
            "mode": mode,
            "current_state": "GREETING",  # Initialize State
            "question_count": 0,          # Initialize Counter
            "chat_history": []
        }
        
        return session_id

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        return SESSIONS.get(session_id)

    @staticmethod
    def update_session_state(session_id: str, new_state: str):
        session = SESSIONS.get(session_id)
        if session:
            session["current_state"] = new_state

    @staticmethod
    def increment_question_count(session_id: str):
        session = SESSIONS.get(session_id)
        if session:
            session["question_count"] += 1

    @staticmethod
    def add_message(session_id: str, role: str, content: str):
        session = SESSIONS.get(session_id)
        if session:
            session["chat_history"].append({"role": role, "content": content})

    @staticmethod
    def get_history(session_id: str) -> List[Dict[str, str]]:
        session = SESSIONS.get(session_id)
        return session.get("chat_history", []) if session else []

    @staticmethod
    def mark_session_finished(session_id: str):
        session = SESSIONS.get(session_id)
        if session:
            session["current_state"] = "FINISHED"