# build system prompt to implement different interview phases (intro, technical questions, HR questions, closing)
import json
from typing import Dict, List, Any

class InterviewManager:
    # State Constants
    GREETING = "GREETING"
    INTRODUCTION = "INTRODUCTION"
    QUESTIONS = "QUESTIONS"
    CLOSING = "CLOSING"

    @staticmethod
    def get_state_classifier_prompt(history: List[Dict], user_input: str, current_state: str) -> str:
        """
        Prompt to determine if we should transition to the next state.
        """
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]])
        
        return f"""
        Analyze the interview progress. 
        Current State: {current_state}
        
        Recent History:
        {history_text}
        
        Candidate's Latest Input: "{user_input}"

        Your task is to decide the next state. Follow these rules:
        - If state is GREETING: Move to INTRODUCTION if the candidate has acknowledged the greeting.
        - If state is INTRODUCTION: Move to QUESTIONS once the candidate has introduced themselves or agreed to start.
        - If state is QUESTIONS: Move to CLOSING if the candidate says they have no more to add, asks to finish, or if the interviewer has already covered several topics.
        - Otherwise: Stay in the {current_state} state.

        Respond with ONLY one word from this list: [GREETING, INTRODUCTION, QUESTIONS, CLOSING]
        """

    @staticmethod
    def get_main_system_prompt(cv_data: dict, job_position: str, mode: str, state: str) -> str:
        """
        The master prompt for generating the actual response.
        """
        cv_summary = f"Name: {cv_data.get('name')}. Skills: {', '.join(cv_data.get('skills', []))}."
        
        role_desc = (
            "Senior Technical Lead" if mode == "technical" 
            else "HR Recruiter"
        )

        state_instructions = {
            "GREETING": f"Start the session. Welcome the candidate warmly to the {job_position} interview.",
            "INTRODUCTION": "Briefly explain that you'll ask a few questions and ask them to give a quick overview of their background.",
            "QUESTIONS": "Ask ONE specific question at a time. Acknowledge their previous point briefly, then dive into a technical or behavioral topic based on their CV.",
            "CLOSING": "The interview is over. Thank them for their time, mention that the team will be in touch, and say goodbye. Do not ask more questions."
        }

        return f"""
        Role: {role_desc}
        Context: Interviewing for {job_position}.
        Candidate Profile: {cv_summary}
        Current Phase: {state}

        Goal: {state_instructions.get(state)}

        Constraints:
        - Use a spoken, natural style (suitable for Text-to-Speech).
        - NEVER use markdown formatting like bolding, bullet points, or lists.
        - Be concise: keep responses under 3 sentences if possible.
        - Do not break character.
        """