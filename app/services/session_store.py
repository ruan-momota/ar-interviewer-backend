# app/services/session_store.py

import json
from typing import List, Dict, Optional
from sqlmodel import Session, select, desc
from app.models import InterviewSession, Candidate, ChatMessage, JobProfile

class SessionManager:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, cv_data: dict, job_position: str, mode: str) -> str:
        """
        Init a interview session, save candidates and generate a system prompt.
        """
        # create or get job profile
        job = self.db.exec(select(JobProfile).where(JobProfile.title == job_position)).first()
        if not job:
            # generate system prompt
            sys_prompt_text = self._build_system_prompt_text(cv_data, job_position, mode)
            job = JobProfile(
                title=job_position,
                system_prompt=sys_prompt_text,
                description=f"Auto-generated for {mode} mode"
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)

        # Create candidate
        skills_str = json.dumps(cv_data.get("skills", []))
        
        candidate = Candidate(
            name=cv_data.get("name", "Unknown Candidate"),
            email=cv_data.get("email"),
            skills=skills_str,
            raw_text=str(cv_data)
        )
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)

        # Create InterviewSession
        session = InterviewSession(
            candidate_id=candidate.id,
            job_profile_id=job.id,
            status="init"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # System prompt as the first message
        self.add_message(session.id, "system", job.system_prompt)

        return session.id

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        return self.db.get(InterviewSession, session_id)

    def add_message(self, session_id: str, role: str, content: str):
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()

    def get_messages_for_llm(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get all messages and turn to list that LLM can accept
        """
        statement = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
        results = self.db.exec(statement).all()
        
        messages = []
        for msg in results:
            messages.append({"role": msg.role, "content": msg.content})
        
        return messages

    def mark_session_finished(self, session_id: str):
        session = self.get_session(session_id)
        if session:
            session.status = "finished"
            self.db.add(session)
            self.db.commit()

    def _build_system_prompt_text(self, cv: dict, job: str, mode: str) -> str:
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