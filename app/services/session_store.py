# app/services/session_store.py

import json
from typing import List, Dict, Optional
from sqlmodel import Session, select, desc
from app.models import (
    InterviewSession, Candidate, ChatMessage, JobProfile,
    PromptTemplate
)


class SessionManager:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, cv_data: dict, job_position: str, mode: str) -> str:
        # ensure there is template in db
        self._ensure_default_templates()

        # get JobProfile
        job = self.db.exec(select(JobProfile).where(JobProfile.title == job_position)).first()
        if not job:
            prompt_text = self._build_system_prompt(cv_data, job_position, mode)
            job = JobProfile(
                title=job_position,
                system_prompt=prompt_text,
                description=f"Auto-generated for {mode} mode"
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
        else:
            prompt_text = self._build_system_prompt(cv_data, job_position, mode)
            # update job prompt (optional)
            job.system_prompt = prompt_text
            self.db.add(job)
            self.db.commit()

        # create candidate
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

        # create session
        session = InterviewSession(
            candidate_id=candidate.id,
            job_profile_id=job.id,
            status="init"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        self.add_message(session.id, "system", prompt_text)

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
        statement = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.id)
        results = self.db.exec(statement).all()
        return [{"role": msg.role, "content": msg.content} for msg in results]

    def mark_session_finished(self, session_id: str):
        session = self.get_session(session_id)
        if session:
            session.status = "finished"
            self.db.add(session)
            self.db.commit()

    def _build_system_prompt(self, cv: dict, job_title: str, mode: str) -> str:
        """
        read template from db
        """
        template_name = mode.lower() 
        template = self.db.exec(select(PromptTemplate).where(PromptTemplate.name == template_name)).first()

        if not template:
            template = self.db.exec(select(PromptTemplate).where(PromptTemplate.name == "default")).first()

        if not template:
            base_text = "You are an interviewer. Evaluate the candidate."
        else:
            base_text = template.template_text

        # prepare data
        skills_list = cv.get('skills', [])
        if isinstance(skills_list, list):
            skills_str = ", ".join(skills_list)
        else:
            skills_str = str(skills_list)

        # replace placeholder
        prompt = base_text.replace("{name}", cv.get('name', 'Candidate')) \
                          .replace("{skills}", skills_str) \
                          .replace("{job_title}", job_title)

        return prompt

    def _ensure_default_templates(self):
        existing = self.db.exec(select(PromptTemplate)).first()
        if existing:
            return

        # define default template
        technical_prompt = (
            "You are a Senior Technical Lead interviewing {name} for the position of {job_title}. "
            "The candidate has the following skills: {skills}. "
            "Your goal is to assess their technical depth. "
            "Start by asking about their most complex project. "
            "Keep questions short and spoken-style. Do NOT use markdown formatting."
        )

        hr_prompt = (
            "You are an HR Manager interviewing {name} for the position of {job_title}. "
            "Skills: {skills}. "
            "Focus on cultural fit, teamwork, and soft skills. "
            "Be polite, encouraging, and professional. "
            "Keep responses concise (1-2 sentences)."
        )

        t1 = PromptTemplate(name="technical", template_text=technical_prompt, description="Hard skills focus")
        t2 = PromptTemplate(name="hr", template_text=hr_prompt, description="Soft skills focus")
        t3 = PromptTemplate(name="default", template_text=hr_prompt, description="Fallback")

        self.db.add(t1)
        self.db.add(t2)
        self.db.add(t3)
        self.db.commit()