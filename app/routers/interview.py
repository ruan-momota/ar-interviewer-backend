from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.schemas.interview import (
    InterviewInitRequest, InterviewInitResponse, 
    InterviewNextRequest, InterviewNextResponse,
    InterviewReplyRequest, InterviewReplyResponse,
    InterviewReportResponse, InterviewEndRequest,
    InterviewEndResponse
)
from app.services.session_store import SessionManager
from app.services.llm_service import (
    generate_interview_question, generate_quick_feedback, 
    generate_evaluation_report, generate_closing_remark
)

router = APIRouter(prefix="/v1/interview", tags=["Interview"])

def analyze_voice_metrics(metrics: List[Dict[str, float]], baselines: Dict[str, float]) -> str:
    if not metrics:
        return "No audio data was collected during this session."
        
    # Pitch can be tricky to judge, so left out for now
    avg_wpm = sum(m['wpm'] for m in metrics) / len(metrics)
    avg_vol = sum(m['volume'] for m in metrics) / len(metrics)
    base_wpm = baselines.get("wpm", 130.0)
    base_vol = baselines.get("volume", 0.05)

    feedback_parts = []
    
    if avg_wpm > base_wpm * 1.35:
        feedback_parts.append(f"You spoke much faster ({int(avg_wpm)} WPM) than your baseline\n({int(base_wpm)} WPM). Fast talking often indicates nervousness.\n")
    elif avg_wpm < base_wpm * 0.65:
        feedback_parts.append(f"You spoke much slower ({int(avg_wpm)} WPM) than your baseline\n({int(base_wpm)} WPM). You might be overthinking your answers.\n")
    else:
        feedback_parts.append(f"Your speaking pace ({int(avg_wpm)} WPM) was consistent, good job!\n")

    # Volume fluctuates more, so a wider threshold is given
    if avg_vol < base_vol * 0.5:
        feedback_parts.append("You were much quieter. Projecting can help demonstrate authority.")
    elif avg_vol > base_vol * 1.5:
        feedback_parts.append("You were much louder than normal. Shouting can radiate unneccesary hostility.")
    else:
        feedback_parts.append("Your vocal volume remained steady and consistent.")
    
    return "".join(feedback_parts)

@router.post("/init", response_model=InterviewInitResponse)
async def init_interview(request: InterviewInitRequest):
    try:
        # Turns Pydantic model into dictionary
        cv_dict = request.cv_data.model_dump()
        
        session_id = SessionManager.create_session(
            cv_data=cv_dict,
            job_position=request.job_position,
            mode=request.interviewer_mode
        )
        
        # Initializes voice metrics list
        session = SessionManager.get_session(session_id)
        if session:
            session["voice_metrics"] = []
            session["baselines"] = {
                "volume": request.baseline_volume,
                "wpm": request.baseline_wpm
            }

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
    
    # Saves audio stats
    if "voice_metrics" not in session:
        session["voice_metrics"] = []

    session["voice_metrics"].append({
        "volume": request.volume,
        "pitch": request.pitch,
        "wpm": request.wpm
    })

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
    
    voice_metrics = session.get("voice_metrics", [])
    baselines = session.get("baselines", {}) # Default to empty dictionary if missing
    voice_feedback = analyze_voice_metrics(voice_metrics, baselines)
    
    return InterviewReportResponse(
        session_id=session_id,
        score=report_data.get("score", 0),
        feedback_summary=report_data.get("feedback_summary", "No summary available."),
        strengths=report_data.get("strengths", []),
        areas_for_improvement=report_data.get("areas_for_improvement", []),
        mission=report_data.get("mission", "Keep practicing!"),
        voice_analysis=voice_feedback
    )

@router.post("/end", response_model=InterviewEndResponse)
async def end_interview(request: InterviewEndRequest):
    session = SessionManager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = SessionManager.get_messages_for_llm(request.session_id)
    end_text = generate_closing_remark(messages)
    
    SessionManager.add_message(request.session_id, "assistant", end_text)
    SessionManager.mark_session_finished(request.session_id)
    
    return InterviewEndResponse(
        session_id=request.session_id,
        end_text=end_text,
        message="Interview session ended."
    )