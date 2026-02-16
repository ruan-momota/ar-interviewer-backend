from pydantic import BaseModel
from typing import List, Optional
from app.schemas.cv import CVData
from enum import Enum

class InterviewPhase(str, Enum):
    GREETING = "GREETING"
    INTRODUCTION = "INTRODUCTION"
    QUESTIONS = "QUESTIONS"
    CLOSING = "CLOSING"

class InterviewState:
    # ...existing code...
    current_phase: InterviewPhase = InterviewPhase.GREETING
    phase_transitions: dict = {}
    
class InterviewInitRequest(BaseModel):
    cv_data: CVData       
    job_position: str    
    job_description: Optional[str] = None 
    interviewer_mode: str = "social"

class InterviewInitResponse(BaseModel):
    session_id: str
    message: str   

class InterviewNextRequest(BaseModel):
    session_id: str

class InterviewNextResponse(BaseModel):
    session_id: str
    interviewer_text: str
    message_type: str = "question"

class InterviewReplyRequest(BaseModel):
    session_id: str
    user_text: str

class InterviewReplyResponse(BaseModel):
    session_id: str
    feedback: str 

class InterviewReportResponse(BaseModel):
    session_id: str
    score: int                  # 0-100
    feedback_summary: str       # total feedback
    strengths: List[str]        # bullets points
    areas_for_improvement: List[str] 
    mission: str 

class InterviewEndRequest(BaseModel):
    session_id: str

class InterviewEndResponse(BaseModel):
    session_id: str
    end_text: str 
    message: str 