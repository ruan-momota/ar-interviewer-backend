from app.schemas.interview import InterviewPhase

class InterviewManager:
    
    PHASE_TRANSITIONS = {
        InterviewPhase.GREETING: {
            "message": "Thank you for that warm greeting! Now, let me introduce myself and explain how this interview will proceed.",
            "next_phase": InterviewPhase.INTRODUCTION
        },
        InterviewPhase.INTRODUCTION: {
            "message": "Great! Now that we've covered the basics, let's dive into some questions about your experience and skills.",
            "next_phase": InterviewPhase.QUESTIONS
        },
        InterviewPhase.QUESTIONS: {
            "message": "Thank you for your detailed responses. Let's wrap up our interview now.",
            "next_phase": InterviewPhase.CLOSING
        },
        InterviewPhase.CLOSING: {
            "message": "Thank you for your time today. This concludes our interview. You'll hear back from us soon!",
            "next_phase": None
        }
    }
    
    def __init__(self):
        self.current_phase = InterviewPhase.GREETING
        self.question_count = 0
        self.max_questions_per_phase = 3  # Configurable
    
    def should_transition_phase(self) -> bool:
        """Determine if we should move to the next phase"""
        if self.current_phase == InterviewPhase.GREETING:
            return self.question_count >= 1
        elif self.current_phase == InterviewPhase.INTRODUCTION:
            return self.question_count >= 2
        elif self.current_phase == InterviewPhase.QUESTIONS:
            return self.question_count >= self.max_questions_per_phase
        return False
    
    def get_transition_message(self) -> dict:
        """Get the transition message for current phase"""
        transition = self.PHASE_TRANSITIONS.get(self.current_phase)
        if transition:
            return {
                "is_transition": True,
                "phase_from": self.current_phase,
                "phase_to": transition["next_phase"],
                "message": transition["message"]
            }
        return None
    
    def transition_to_next_phase(self):
        """Move to the next interview phase"""
        transition = self.PHASE_TRANSITIONS.get(self.current_phase)
        if transition and transition["next_phase"]:
            self.current_phase = transition["next_phase"]
            self.question_count = 0
            return True
        return False
    
    async def process_response(self, user_message: str) -> dict:
        """Process user response and handle phase transitions"""
        # ...existing code for processing response...
        
        self.question_count += 1
        
        # Check if we need to transition
        if self.should_transition_phase():
            transition_msg = self.get_transition_message()
            self.transition_to_next_phase()
            return {
                "response": ai_response,
                "transition": transition_msg,
                "current_phase": self.current_phase
            }
        
        return {
            "response": ai_response,
            "transition": None,
            "current_phase": self.current_phase
        }