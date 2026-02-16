from pydantic import BaseModel
from typing import List, Optional
from app.schemas.cv import CVData

class InterviewInitRequest(BaseModel):
    cv_data: CVData       
    job_position: str    
    job_description: Optional[str] = None 
    interviewer_mode: str = "social"

    baseline_volume: float
    baseline_wpm: float
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
    volume: float = 0.0
    pitch: float = 0.0
    wpm: float = 0.0

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
    voice_analysis: str

class InterviewEndRequest(BaseModel):
    session_id: str

class InterviewEndResponse(BaseModel):
    session_id: str
    end_text: str 
    message: str 