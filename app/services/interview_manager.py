from typing import Dict, List

class InterviewManager:
    # State Constants
    GREETING = "GREETING"
    INTRODUCTION = "INTRODUCTION"
    QUESTIONS = "QUESTIONS"
    CLOSING = "CLOSING"

    @staticmethod
    def get_state_classifier_prompt(history: List[Dict], user_input: str, current_state: str, q_count: int) -> str:
        """
        Prompt to determine if we should transition to the next state.
        """
        # We only look at the last 2 turns to save tokens, plus the immediate user input
        recent_history = history[-4:] if len(history) > 4 else history
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in recent_history])
        
        return f"""
        You are the Logic Engine for an interview bot. 
        Current State: {current_state}
        Questions Asked So Far: {q_count} (Max limit is 4)
        
        Recent Chat History:
        {history_text}
        
        Candidate's Latest Input: "{user_input}"

        DECISION RULES:
        1. IF GREETING: Move to INTRODUCTION if candidate says "hi", "hello", or acknowledges.
        2. IF INTRODUCTION: Move to QUESTIONS if candidate introduces themselves or says "ready".
        3. IF QUESTIONS: 
           - Move to CLOSING if {q_count} >= 4 (Max limit reached).
           - Move to CLOSING if candidate says "I'm done", "stop", or "no more questions".
           - Otherwise, stay in QUESTIONS.
        4. IF CLOSING: Stay in CLOSING.

        OUTPUT:
        Respond with ONLY one word from this list: [GREETING, INTRODUCTION, QUESTIONS, CLOSING]
        """

    @staticmethod
    def get_main_system_prompt(cv_data: dict, job_position: str, mode: str, state: str, q_count: int) -> str:
        """
        The master prompt for generating the actual response.
        """
        cv_summary = f"Name: {cv_data.get('name', 'Candidate')}. Skills: {', '.join(cv_data.get('skills', []))}."
        
        role_desc = (
            "Senior Technical Lead. Focus on hard skills, architecture, and coding." 
            if mode == "technical" 
            else "HR Recruiter. Focus on soft skills, culture fit, and motivation."
        )

        # Dynamic instructions based on State
        if state == "GREETING":
            instruction = f"Welcome the candidate to the {job_position} interview. Be professional and warm."
        elif state == "INTRODUCTION":
            instruction = "Explain that you will ask 4 specific questions. Ask the candidate to briefly introduce themselves."
        elif state == "QUESTIONS":
            instruction = (
                f"This is Question {q_count + 1} of 4. "
                "First, acknowledge their previous answer (briefly, 1 sentence). "
                "Then, ask a NEW specific question based on their CV skills or the Job Description. "
                "Do NOT ask multiple questions."
            )
        elif state == "CLOSING":
            instruction = "The interview is finished. Thank them for their time. Say that the team will review the results. Do not ask more questions."
        else:
            instruction = "Be polite."

        return f"""
        Role: {role_desc}
        Context: Interviewing for {job_position}.
        Candidate Profile: {cv_summary}
        
        CURRENT GOAL: {instruction}

        Constraints:
        - Speak naturally (suitable for Text-to-Speech).
        - NO Markdown (no bolding, no bullet points, no lists).
        - Keep responses concise (under 50 words).
        - Do not break character.
        """