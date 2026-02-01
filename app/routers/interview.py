from fastapi import APIRouter, HTTPException
from app.schemas.interview import InterviewInitRequest, InterviewInitResponse
from app.services.session_store import SessionManager

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