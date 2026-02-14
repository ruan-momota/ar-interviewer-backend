from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime,timezone
import uuid

class JobProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str  # e.g. "Python Backend Developer"
    description: Optional[str] = None
    system_prompt: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    sessions: List["InterviewSession"] = Relationship(back_populates="job_profile")

class Candidate(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(default="Unknown")
    email: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None 
    
    skills: str = Field(default="[]")
    education_json: str = Field(default="[]")  
    experience_json: str = Field(default="[]") 
    projects_json: str = Field(default="[]") 
    
    raw_text: Optional[str] = Field(default=None)
    
    sessions: List["InterviewSession"] = Relationship(back_populates="candidate")

# Interview session table
class InterviewSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # Foreign key
    candidate_id: Optional[str] = Field(default=None, foreign_key="candidate.id")
    job_profile_id: Optional[int] = Field(default=None, foreign_key="jobprofile.id")
    
    # Interview status
    status: str = Field(default="init")  # init, ongoing, finished, aborted
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    
    # Evaluation report
    report_json: Optional[str] = None
    score: int = Field(default=0)
    
    # Assosiation
    candidate: Optional[Candidate] = Relationship(back_populates="sessions")
    job_profile: Optional[JobProfile] = Relationship(back_populates="sessions")
    messages: List["ChatMessage"] = Relationship(back_populates="session")

# Chat history
class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="interviewsession.id")
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    session: Optional[InterviewSession] = Relationship(back_populates="messages")