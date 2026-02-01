import json
from groq import Groq
from app.config import settings
from app.schemas.cv import CVData

client = Groq(api_key=settings.GROQ_API_KEY)

def parse_cv_with_groq(text: str) -> dict:
    # CVData.model_json_schema()
    system_prompt = "You are a resume parser. Output strict JSON."
    user_prompt = f"Extract CV data from this text:\n{text[:15000]}"
    
    schema_structure = json.dumps(CVData.model_json_schema(), indent=2)
    user_prompt += f"\n\nMatch this JSON schema:\n{schema_structure}"

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"LLM Error: {e}")
        raise e