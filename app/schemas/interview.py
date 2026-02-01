from pydantic import BaseModel
from typing import Optional
from app.schemas.cv import CVData

class InterviewInitRequest(BaseModel):
    cv_data: CVData       
    job_position: str    
    job_description: Optional[str] = None 
    interviewer_mode: str = "social"

class InterviewInitResponse(BaseModel):
    session_id: str
    message: str   