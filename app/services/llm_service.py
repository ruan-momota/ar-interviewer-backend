import json
import httpx
from groq import Groq
from openai import OpenAI
from app.config import settings
from app.schemas.cv import CVData
from app.schemas.interview import InterviewPhase

http_client = httpx.Client(transport=httpx.HTTPTransport(local_address="0.0.0.0"))

if settings.LLM_PROVIDER == "ollama":
    client = OpenAI(
        base_url=settings.OLLAMA_BASE_URL,
        api_key="ollama",
        http_client=http_client
    )
    MODEL_NAME = settings.OLLAMA_MODEL
else:
    client = Groq(
        api_key=settings.GROQ_API_KEY,
        http_client=http_client
    )
    MODEL_NAME = "llama-3.3-70b-versatile"

class LLMService:
    
    PHASE_PROMPTS = {
        InterviewPhase.GREETING: "You are in the greeting phase. Be warm and welcoming. Ask about their day.",
        InterviewPhase.INTRODUCTION: "Introduce yourself as an AI interviewer. Explain the interview structure briefly.",
        InterviewPhase.QUESTIONS: "Ask relevant technical and behavioral questions based on the candidate's CV.",
        InterviewPhase.CLOSING: "Thank the candidate and provide next steps information."
    }
    
    def get_system_prompt(self, phase: InterviewPhase, cv_data: dict = None) -> str:
        """Generate phase-specific system prompt"""
        base_prompt = "You are an AI interviewer conducting a professional job interview."
        phase_instruction = self.PHASE_PROMPTS.get(phase, "")
        
        return f"{base_prompt}\n\n{phase_instruction}\n\nCV Data: {cv_data}"

def parse_cv_with_llm(text: str) -> dict:
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
    transcript = ""
    for msg in history:
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        transcript += f"{role}: {msg['content']}\n\n"

    schema_structure = {
        "score": 85,
        "feedback_summary": "Good content but answers were too vague.",
        "strengths": ["Polite tone", "Good vocabulary"],
        "areas_for_improvement": ["Answers lacked metrics", "Did not ask questions back"],
        "mission": "Include specific metrics (numbers/%) in your project descriptions."
    }

    system_prompt = (
        "You are an expert Interview Coach. "
        "Analyze the transcript based ONLY on the text content. "
        "You cannot see or hear the candidate. "
        "Output ONLY valid JSON."
    )

    user_prompt = (
        f"Target Job Position: {job_position}\n\n"
        f"INTERVIEW TRANSCRIPT:\n{transcript}\n\n"
        f"Analyze the candidate's performance based on text content (clarity, structure, specificity).\n\n"
        f"IMPORTANT GUIDELINES FOR 'mission' FIELD:\n"
        f"1. It must be ONE single, actionable task for the NEXT interview.\n"
        f"2. **CRITICAL**: Since you interact via text only, DO NOT mention body language, eye contact, voice tone, or appearance.\n"
        f"3. Focus on: Answer Structure (e.g., STAR method), Specificity (using numbers/tools), Length (conciseness), or Interaction (asking questions).\n"
        f"4. Start with a VERB. Max 15 words.\n"
        f"5. Example GOOD missions: 'Use the STAR method for one answer', 'Mention 3 specific technical tools', 'Keep answers under 5 sentences'.\n\n"
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
            "mission": "Provide a concrete example when answering." 
        }

def generate_closing_remark(messages: list) -> str:
    try:
        context_messages = messages.copy()
        
        system_instruction = (
            "The interview is over. "
            "Generate a polite, professional closing statement (1-2 sentences). "
            "Thank the candidate for their time and mention that you will be in touch. "
            "Do not ask any more questions."
        )
        
        context_messages.append({"role": "system", "content": system_instruction})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=context_messages,
            temperature=0.6,
            max_tokens=60
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Closing Error: {e}")
        return "Thank you for your time. We will be in touch shortly."