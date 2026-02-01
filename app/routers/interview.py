from fastapi import APIRouter, HTTPException
from app.schemas.interview import (
    InterviewInitRequest, InterviewInitResponse, 
    InterviewNextRequest, InterviewNextResponse,
    InterviewReplyRequest, InterviewReplyResponse,
    InterviewReportResponse
)
from app.services.session_store import SessionManager
from app.services.llm_service import generate_interview_question, generate_quick_feedback, generate_evaluation_report

router = APIRouter(prefix="/v1/interview", tags=["Interview"])

@router.post("/init", response_model=InterviewInitResponse)
async def init_interview(request: InterviewInitRequest):
    try:
        # turn Pydantic model into dict
        cv_dict = request.cv_data.model_dump()
        
        session_id = SessionManager.create_session(
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
        raise HTTPException(status_code=500, detail="Failed to initialize interview session.")

@router.post("/next", response_model=InterviewNextResponse)
async def next_question(request: InterviewNextRequest):
    session = SessionManager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = SessionManager.get_messages_for_llm(request.session_id)
    ai_text = generate_interview_question(messages)
    SessionManager.add_message(request.session_id, "assistant", ai_text)
    
    return InterviewNextResponse(
        session_id=request.session_id,
        interviewer_text=ai_text
    )

@router.post("/reply", response_model=InterviewReplyResponse)
async def reply_interview(request: InterviewReplyRequest):
    session = SessionManager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    SessionManager.add_message(request.session_id, "user", request.user_text)
    messages = SessionManager.get_messages_for_llm(request.session_id)
    feedback_text = generate_quick_feedback(messages)
    SessionManager.add_message(request.session_id, "assistant", feedback_text)
    
    return InterviewReplyResponse(
        session_id=request.session_id,
        feedback=feedback_text
    )

@router.get("/report/{session_id}", response_model=InterviewReportResponse)
async def get_interview_report(session_id: str):
    session = SessionManager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history = session["chat_history"]
    job_position = session["job"]
    
    if not history:
        raise HTTPException(status_code=400, detail="No interview history found to analyze.")

    report_data = generate_evaluation_report(history, job_position)
    
    return InterviewReportResponse(
        session_id=session_id,
        score=report_data.get("score", 0),
        feedback_summary=report_data.get("feedback_summary", "No summary available."),
        strengths=report_data.get("strengths", []),
        areas_for_improvement=report_data.get("areas_for_improvement", []),
        key_suggestion=report_data.get("key_suggestion", "Keep practicing!")
    )