from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.database import get_session
from app.services.session_store import SessionManager
from app.schemas.interview import (
    InterviewInitRequest, InterviewInitResponse, 
    InterviewNextRequest, InterviewNextResponse,
    InterviewReplyRequest, InterviewReplyResponse,
    InterviewReportResponse, InterviewEndRequest,
    InterviewEndResponse
)
from app.services.llm_service import (
    generate_interview_question, generate_quick_feedback, 
    generate_evaluation_report, generate_closing_remark
)

router = APIRouter(prefix="/v1/interview", tags=["Interview"])

def get_session_manager(db: Session = Depends(get_session)) -> SessionManager:
    return SessionManager(db)

@router.post("/init", response_model=InterviewInitResponse)
async def init_interview(
    request: InterviewInitRequest,
    manager: SessionManager = Depends(get_session_manager) # 注入 manager
):
    try:
        cv_dict = request.cv_data.model_dump()
        session_id = manager.create_session(
            cv_data=cv_dict,
            job_position=request.job_position,
            mode=request.interviewer_mode
        )
        
        return InterviewInitResponse(
            session_id=session_id,
            message="Interview session initialized successfully."
        )
    except Exception as e:
        print(f"Init Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/next", response_model=InterviewNextResponse)
async def next_question(
    request: InterviewNextRequest,
    manager: SessionManager = Depends(get_session_manager)
):
    session = manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = manager.get_messages_for_llm(request.session_id)
    ai_text = generate_interview_question(messages)
    
    manager.add_message(request.session_id, "assistant", ai_text)
    
    return InterviewNextResponse(
        session_id=request.session_id,
        interviewer_text=ai_text
    )

@router.post("/reply", response_model=InterviewReplyResponse)
async def reply_interview(
    request: InterviewReplyRequest,
    manager: SessionManager = Depends(get_session_manager)
):
    session = manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    manager.add_message(request.session_id, "user", request.user_text)
    
    messages = manager.get_messages_for_llm(request.session_id)
    feedback_text = generate_quick_feedback(messages)
    
    manager.add_message(request.session_id, "assistant", feedback_text)
    
    return InterviewReplyResponse(
        session_id=request.session_id,
        feedback=feedback_text
    )

@router.get("/report/{session_id}", response_model=InterviewReportResponse)
async def get_interview_report(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = manager.get_messages_for_llm(session_id)
    job_position = session.job_profile.title if session.job_profile else "Unknown Position"
    
    if not history:
        raise HTTPException(status_code=400, detail="No interview history found.")

    report_data = generate_evaluation_report(history, job_position)
    
    # TODO (Optional): 可以把 report_data 保存回 session.report_json
    
    return InterviewReportResponse(
        session_id=session_id,
        score=report_data.get("score", 0),
        feedback_summary=report_data.get("feedback_summary", "No summary available."),
        strengths=report_data.get("strengths", []),
        areas_for_improvement=report_data.get("areas_for_improvement", []),
        mission=report_data.get("mission", "Keep practicing!")
    )

@router.post("/end", response_model=InterviewEndResponse)
async def end_interview(
    request: InterviewEndRequest,
    manager: SessionManager = Depends(get_session_manager)
):
    session = manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = manager.get_messages_for_llm(request.session_id)
    end_text = generate_closing_remark(messages)
    
    manager.add_message(request.session_id, "assistant", end_text)
    manager.mark_session_finished(request.session_id)
    
    return InterviewEndResponse(
        session_id=request.session_id,
        end_text=end_text,
        message="Interview session ended."
    )