from pypdf import PdfReader
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join([p.extract_text() or "" for p in reader.pages])
        return text.strip()
    except Exception as e:
        print(f"PDF Error: {e}")
        return ""