from pydantic import BaseModel
from typing import List, Optional

class CandidateListSchema(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    job_title: Optional[str] = None
    created_at: str = "2024-01-01"

class InterviewListSchema(BaseModel):
    id: str
    candidate_name: str
    job_title: str
    status: str
    score: int
    start_time: str

class InterviewDetailSchema(InterviewListSchema):
    messages: List[dict]
    report: Optional[dict] = None

class PromptTemplateCreate(BaseModel):
    name: str
    template_text: str
    description: Optional[str] = None

# --- Dashboard Schema ---
class DashboardStatsSchema(BaseModel):
    total_candidates: int
    total_interviews: int
    interviews_today: int
    average_score: float
    recent_trend: List[dict] # [{"date": "2023-10-01", "count": 5}, ...]