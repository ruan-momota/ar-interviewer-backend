from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_service import parse_cv_with_groq
from app.schemas.cv import CVData

router = APIRouter(prefix="/v1/cv", tags=["CV Parsing"])

@router.post("/parse", response_model=CVData)
async def parse_cv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")

    pdf_bytes = await file.read()
    text = extract_text_from_pdf(pdf_bytes)

    if len(text) < 50:
        raise HTTPException(status_code=400, detail="Empty or scanned PDF")

    try:
        data = parse_cv_with_groq(text)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))