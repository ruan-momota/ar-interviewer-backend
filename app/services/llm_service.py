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

def generate_interview_question(messages: list) -> str:
    """
    Generate next question based on chat history.
    """
    try:
        if len(messages) == 1:
            messages.append({"role": "user", "content": "I am ready for the interview. Please start."})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=150   # limit length
        )
        
        response_text = completion.choices[0].message.content
        return response_text
        
    except Exception as e:
        print(f"LLM Question Generation Error: {e}")
        return "Could you please tell me a bit more about yourself?"

def generate_quick_feedback(messages: list) -> str:
    """
    A short feedback based on user's answer.
    """
    try:
        context_messages = messages.copy()
        
        system_instruction = (
            "You are the interviewer. The candidate just gave an answer. "
            "Give a very short, natural reaction (2-5 words) to acknowledge their answer. "
            "Examples: 'I see.', 'That makes sense.', 'Interesting point.', 'Okay, understood.'. "
            "Do NOT ask a new question yet. Just acknowledge."
        )
        
        context_messages.append({"role": "system", "content": system_instruction})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=context_messages,
            temperature=0.6,
            max_tokens=30
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Feedback Error: {e}")
        return "I see."

def generate_evaluation_report(history: list, job_position: str) -> dict:
    # turns chat history into transcript
    transcript = ""
    for msg in history:
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        transcript += f"{role}: {msg['content']}\n\n"

    schema_structure = {
        "score": 85,
        "feedback_summary": "Overall good performance...",
        "strengths": ["Clear communication", "Strong technical knowledge"],
        "areas_for_improvement": ["Lack of specific examples", "Speaking too fast"],
        "key_suggestion": "Try to use the STAR method for behavioral questions."
    }

    system_prompt = (
        "You are an expert Interview Coach and Recruiter. "
        "Your task is to analyze the following interview transcript and provide a structured evaluation report. "
        "Be constructive, professional, and specific. "
        "Output ONLY valid JSON."
    )

    user_prompt = (
        f"Target Job Position: {job_position}\n\n"
        f"INTERVIEW TRANSCRIPT:\n{transcript}\n\n"
        f"Analyze the candidate's performance based on: clarity, relevance, confidence, and content.\n"
        f"Return a JSON object matching this structure:\n{json.dumps(schema_structure)}"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content)

    except Exception as e:
        print(f"LLM Report Error: {e}")
        return {
            "score": 0,
            "feedback_summary": "Error generating report.",
            "strengths": [],
            "areas_for_improvement": [],
            "key_suggestion": "Please try again."
        }