from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from typing import List, Optional
from app.database import get_session
from app.models import Candidate, InterviewSession, ChatMessage
from app.schemas.admin import (
    CandidateListSchema, InterviewListSchema, InterviewDetailSchema
)

router = APIRouter(prefix="/v1/admin", tags=["Admin Console"])

@router.get("/candidates", response_model=List[CandidateListSchema])
async def get_all_candidates(
    skip: int = 0, 
    limit: int = 20, 
    db: Session = Depends(get_session)
):
    
    # select * from candidate order by id desc
    statement = select(Candidate).offset(skip).limit(limit)
    results = db.exec(statement).all()
    
    return [
        CandidateListSchema(
            id=c.id,
            name=c.name,
            email=c.email,
            job_title=c.job_title
        ) for c in results
    ]

@router.get("/interviews", response_model=List[InterviewListSchema])
async def get_all_interviews(
    skip: int = 0, 
    limit: int = 20, 
    db: Session = Depends(get_session)
):
    """get all interview record"""
    statement = select(InterviewSession).order_by(desc(InterviewSession.start_time)).offset(skip).limit(limit)
    results = db.exec(statement).all()
    
    output = []
    for session in results:
        c_name = session.candidate.name if session.candidate else "Unknown"
        j_title = session.job_profile.title if session.job_profile else "Default Position"
        
        output.append(InterviewListSchema(
            id=session.id,
            candidate_name=c_name,
            job_title=j_title,
            status=session.status,
            score=session.score,
            start_time=session.start_time.isoformat()
        ))
    return output

@router.get("/interviews/{session_id}", response_model=InterviewDetailSchema)
async def get_interview_detail(session_id: str, db: Session = Depends(get_session)):
    """get details of interview"""
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    msgs = [{"role": m.role, "content": m.content, "time": m.timestamp.isoformat()} for m in session.messages]
    
    c_name = session.candidate.name if session.candidate else "Unknown"
    j_title = session.job_profile.title if session.job_profile else "Default Position"
    
    report_data = None
    if session.report_json:
        import json
        try:
            report_data = json.loads(session.report_json)
        except:
            pass

    return InterviewDetailSchema(
        id=session.id,
        candidate_name=c_name,
        job_title=j_title,
        status=session.status,
        score=session.score,
        start_time=session.start_time.isoformat(),
        messages=msgs,
        report=report_data
    )