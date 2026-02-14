from pydantic import BaseModel
from typing import List, Optional

class Education(BaseModel):
    degree: str
    school: str
    start: str
    end: str

class Experience(BaseModel):
    title: str
    company: str
    start: str
    end: str
    bullets: List[str]

class Project(BaseModel):
    name: str
    tech: List[str]
    bullets: List[str]

class CVData(BaseModel):
    job_title: str
    name: str
    email: str
    phone: str
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]
    skills: List[str]

class CVResponse(CVData):
    id: str