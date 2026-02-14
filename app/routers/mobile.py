import io
import uuid
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlmodel import Session, select
from app.database import get_session
from app.models import UploadToken, Candidate
from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_service import parse_cv_with_llm
import json
from app.schemas.cv import CVData, CVResponse 

router = APIRouter(prefix="/v1/mobile", tags=["Mobile Upload"])

# generate qrcode
@router.get("/generate_qr")
async def generate_qr_code(
    job_id: int = None, 
    host_ip: str = "192.168.2.107", # should be replaced to correct ip
    db: Session = Depends(get_session)
):
    """
    generate picture of qrcode
    format: http://<host_ip>:8000/v1/mobile/upload_page?token=...
    """
    token_str = str(uuid.uuid4())
    
    upload_token = UploadToken(token=token_str, job_id=job_id)
    db.add(upload_token)
    db.commit()

    url = f"http://{host_ip}:8000/v1/mobile/upload_page?token={token_str}"
    
    # generate image of qrcode
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return StreamingResponse(img_byte_arr, media_type="image/png")

# page on mobile
@router.get("/upload_page", response_class=HTMLResponse)
async def get_upload_page(token: str, db: Session = Depends(get_session)):

    # verify Token
    token_record = db.get(UploadToken, token)
    if not token_record or token_record.is_used:
        return "<h1>Link Expired or Invalid</h1>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload CV</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: sans-serif; padding: 20px; text-align: center; }}
            .btn {{ background: #007bff; color: white; padding: 15px; border: none; border-radius: 5px; font-size: 16px; width: 100%; }}
            input {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h2>AR Interview Upload</h2>
        <p>Please upload your PDF Resume.</p>
        <form action="/v1/mobile/upload_cv" method="post" enctype="multipart/form-data">
            <input type="hidden" name="token" value="{token}">
            <input type="file" name="file" accept=".pdf" required>
            <br><br>
            <button type="submit" class="btn">Upload Resume</button>
        </form>
    </body>
    </html>
    """
    return html_content

# submit endpoint on mobile
@router.post("/upload_cv")
async def mobile_upload_cv(
    token: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_session)
):

    # verify token
    token_record = db.get(UploadToken, token)
    if not token_record or token_record.is_used:
        raise HTTPException(status_code=400, detail="Token Invalid")

    # parse pdf
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF supported")
    
    pdf_bytes = await file.read()
    text = extract_text_from_pdf(pdf_bytes)
    
    # 3. LLM 解析
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
        
        # mark token is used
        token_record.is_used = True
        db.add(token_record)
        
        db.commit()
        
        return {"status": "success", "message": "CV Uploaded! You can put down your phone now."}

    except Exception as e:
        print(f"Mobile Upload Error: {e}")
        raise HTTPException(status_code=500, detail="Parsing Failed")