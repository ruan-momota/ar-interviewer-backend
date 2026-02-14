from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from app.database import get_session
from app.models import Candidate, InterviewSession, ChatMessage, PromptTemplate
from app.schemas.admin import (
    CandidateListSchema, InterviewListSchema, InterviewDetailSchema,
    PromptTemplateCreate, DashboardStatsSchema
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

@router.post("/templates")
async def create_template(t: PromptTemplateCreate, db: Session = Depends(get_session)):
    new_t = PromptTemplate(name=t.name, template_text=t.template_text, description=t.description)
    db.add(new_t)
    db.commit()
    return new_t

@router.get("/templates")
async def get_templates(db: Session = Depends(get_session)):
    return db.exec(select(PromptTemplate)).all()

@router.get("/dashboard/stats", response_model=DashboardStatsSchema)
async def get_dashboard_stats(db: Session = Depends(get_session)):

    total_candidates = db.exec(select(func.count(Candidate.id))).one()
    total_interviews = db.exec(select(func.count(InterviewSession.id))).one()
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    interviews_today = db.exec(
        select(func.count(InterviewSession.id))
        .where(InterviewSession.start_time >= today_start)
    ).one()
    
    # Average score
    avg_score_result = db.exec(
        select(func.avg(InterviewSession.score))
        .where(InterviewSession.score > 0)
    ).one()
    average_score = round(avg_score_result, 1) if avg_score_result else 0.0

    # Last 7 Days Trend
    trend_data = []
    for i in range(6, -1, -1): # 6, 5, 4, 3, 2, 1, 0 (0 is today)
        day_target = today_start - timedelta(days=i)
        next_day = day_target + timedelta(days=1)
        
        count = db.exec(
            select(func.count(InterviewSession.id))
            .where(InterviewSession.start_time >= day_target)
            .where(InterviewSession.start_time < next_day)
        ).one()
        
        trend_data.append({
            "date": day_target.strftime("%Y-%m-%d"),
            "count": count
        })

    return DashboardStatsSchema(
        total_candidates=total_candidates,
        total_interviews=total_interviews,
        interviews_today=interviews_today,
        average_score=average_score,
        recent_trend=trend_data
    )