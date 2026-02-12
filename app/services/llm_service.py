import json
import httpx
from groq import Groq
from openai import OpenAI
from app.config import settings
from app.schemas.cv import CVData
from app.services.interview_manager import InterviewManager
from app.services.session_store import SessionManager

# --- Client Setup ---
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

# --- CV Parsing (Standalone) ---
def parse_cv_with_llm(text: str) -> dict:
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

# --- Main Interview Logic ---
def generate_interview_response(session_id: str, user_input: str) -> str:
    """
    Orchestrates the interview flow:
    1. Saves User Input
    2. Determines Next State (Intent Classification)
    3. Generates Response based on State
    4. Saves Assistant Response
    """
    session = SessionManager.get_session(session_id)
    if not session:
        return "Error: Session expired or not found."

    # 1. Save User Message to History
    SessionManager.add_message(session_id, "user", user_input)

    # 2. Intent Analysis (Classifier)
    # We ask a small LLM call to decide if we switch states based on user input
    classifier_prompt = InterviewManager.get_state_classifier_prompt(
        session["chat_history"], 
        user_input, 
        session["current_state"],
        session["question_count"]
    )
    
    try:
        state_check = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Or use a smaller model like 'llama-3.2-3b' for speed
            messages=[{"role": "user", "content": classifier_prompt}],
            temperature=0,
            max_tokens=10
        )
        new_state = state_check.choices[0].message.content.strip().upper()
        
        # Validate and Update State
        valid_states = [InterviewManager.GREETING, InterviewManager.INTRODUCTION, InterviewManager.QUESTIONS, InterviewManager.CLOSING]
        if new_state in valid_states and new_state != session["current_state"]:
            print(f"State Transition: {session['current_state']} -> {new_state}")
            SessionManager.update_session_state(session_id, new_state)
            
    except Exception as e:
        print(f"Classifier Error: {e}")
        # If classifier fails, we just stay in current state
        pass

    # 3. Response Generation (Interviewer Persona)
    system_prompt = InterviewManager.get_main_system_prompt(
        session["cv"], 
        session["job"], 
        session["mode"], 
        session["current_state"],
        session["question_count"]
    )

    # Combine System Prompt + Chat History
    messages = [{"role": "system", "content": system_prompt}] + session["chat_history"]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=250
        )
        response_text = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Generation Error: {e}")
        response_text = "I apologize, I lost my train of thought. Could you repeat that?"

    # 4. Post-Processing: Save Response & Update Counters
    SessionManager.add_message(session_id, "assistant", response_text)
    
    # If we just asked a question, increment the count
    if session["current_state"] == InterviewManager.QUESTIONS:
        SessionManager.increment_question_count(session_id)
        
    return response_text

# --- Evaluation Report (Post-Interview) ---
def generate_evaluation_report(session_id: str) -> dict:
    session = SessionManager.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
        
    history = session["chat_history"]
    job_position = session["job"]

    transcript = ""
    for msg in history:
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        transcript += f"{role}: {msg['content']}\n\n"

    schema_structure = {
        "score": 85,
        "feedback_summary": "Summary text...",
        "strengths": ["Strength 1", "Strength 2"],
        "areas_for_improvement": ["Weakness 1"],
        "key_suggestion": "Suggestion..."
    }

    system_prompt = "You are an expert Interview Coach. Analyze the transcript and output JSON."
    user_prompt = (
        f"Job: {job_position}\nTRANSCRIPT:\n{transcript}\n"
        f"Return JSON matching:\n{json.dumps(schema_structure)}"
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
        print(f"Report Error: {e}")
        return {"error": "Failed to generate report"}