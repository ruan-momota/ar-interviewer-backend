import uuid
from typing import Dict, Any

# structure { "session_id": { "cv": ..., "job": ..., "history": [] } }
SESSIONS: Dict[str, Any] = {}

class SessionManager:
    @staticmethod
    def create_session(cv_data: dict, job_position: str, mode: str) -> str:
        """
        Init a session.
        """
        session_id = str(uuid.uuid4())
        
        # build system prompt
        system_prompt = SessionManager._build_system_prompt(cv_data, job_position, mode)
        
        # init store structure
        SESSIONS[session_id] = {
            "cv": cv_data,
            "job": job_position,
            "mode": mode,
            "system_prompt": system_prompt,
            "chat_history": []
        }
        
        return session_id

    @staticmethod
    def get_session(session_id: str):
        return SESSIONS.get(session_id)

    @staticmethod
    def _build_system_prompt(cv, job, mode) -> str:
        cv_summary = f"Candidate Name: {cv.get('name')}. "
        cv_summary += f"Skills: {', '.join(cv.get('skills', []))}. "
        
        if mode == "technical":
            role_desc = "You are a Senior Technical Lead. Focus on hard skills, coding knowledge, and project details."
        else:
            role_desc = "You are an HR Recruiter. Focus on soft skills, culture fit, and motivation."

        prompt = (
            f"{role_desc} "
            f"You are interviewing a candidate for the position of {job}. "
            f"Here is the candidate's summary: {cv_summary}. "
            "Your goal is to evaluate them. "
            "Keep your questions concise and spoken-style (suitable for TTS)."
            "Do not output markdown lists, just speak naturally."
        )
        return prompt