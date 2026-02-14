import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlmodel import Session
from app.database import get_session
from app.models import Candidate
from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_service import parse_cv_with_llm
from app.schemas.cv import CVData, CVResponse 

router = APIRouter(prefix="/v1/cv", tags=["CV Parsing"])

@router.post("/parse", response_model=CVResponse)
async def parse_cv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_session)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")

    pdf_bytes = await file.read()
    text = extract_text_from_pdf(pdf_bytes)

    if len(text) < 50:
        raise HTTPException(status_code=400, detail="Empty or scanned PDF")

    try:
        raw_data = parse_cv_with_llm(text)
        cv_obj = CVData(**raw_data)

        candidate = Candidate(
            name=cv_obj.name,
            email=cv_obj.email,
            phone=cv_obj.phone,
            job_title=cv_obj.job_title,
            skills=json.dumps(cv_obj.skills),
            education_json=json.dumps([e.model_dump() for e in cv_obj.education]),
            experience_json=json.dumps([e.model_dump() for e in cv_obj.experience]),
            projects_json=json.dumps([e.model_dump() for e in cv_obj.projects]),
            raw_text=text
        )
        
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        
        response_dict = cv_obj.model_dump()
        response_dict["id"] = candidate.id
        
        return response_dict

    except Exception as e:
        print(f"Parse Error Details: {e}") 
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")