"""CoachCoyote agent for managing the conversation and delivering coaching.

CoachCoyote acts as the voice of the system, integrating drills and feedback
into a natural conversation flow using an LLM.
"""

from typing import List, Dict, Any, Optional
import time

from src.zoo.coaching.task_tiger import Drill
from src.zoo.zoo_logger import get_zoo_logger

class CoachCoyote:
    """The conversational coach agent."""

    def __init__(self, llm_client=None, model_name: str = "llama3.2:3b"):
        """
        Args:
            llm_client: Object with a .generate(prompt) method.
            model_name: Name of the model to use.
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.logger = get_zoo_logger()
        self.system_prompt_template = (
            "You are Rob's English conversation coach. You are friendly, encouraging, but professional.\n\n"
            "Current Focus: {focus}\n"
            "Coach Intensity: {intensity}\n"
            "User Profile: Target CEFR {cefr}, prefers {accent} accent.\n\n"
            "{drill_instruction}\n\n"
            "Conversation History:\n"
            "{history}\n\n"
            "User: {user_utterance}\n\n"
            "Respond naturally to the user. {drill_guidance}"
        )

    def converse(
        self,
        utterance: str,
        context: List[Dict[str, str]],
        focus: str = "general",
        profile: Dict[str, Any] = None,
        intensity: str = "normal"
    ) -> str:
        """Handle a normal conversation turn.
        
        Args:
            utterance: The user's latest input.
            context: List of {"role": "user"|"assistant", "content": "..."}
            focus: Current session focus area.
            profile: User profile data.
            intensity: Coaching intensity level.
            
        Returns:
            The coach's response text.
        """
        response = self._generate_response(
            utterance, context, focus, profile, intensity,
            drill=None
        )
        self.logger.coach_response("CoachCoyote", "conversation", f"Response length: {len(response)} chars")
        return response

    def deliver_drill(
        self,
        drill: Drill,
        utterance: str,
        context: List[Dict[str, str]],
        focus: str = "general",
        profile: Dict[str, Any] = None,
        intensity: str = "normal"
    ) -> str:
        """Inject a drill into the conversation.
        
        Args:
            drill: The drill to deliver.
            utterance: The user's latest input (that triggered the drill).
            context: Conversation history.
            focus: Session focus.
            profile: User profile.
            intensity: Coaching intensity.
            
        Returns:
            The coach's response containing the drill.
        """
        response = self._generate_response(
            utterance, context, focus, profile, intensity,
            drill=drill
        )
        self.logger.coach_response("CoachCoyote", "drill_delivery", f"Drill: {drill.type}")
        return response

    def _generate_response(
        self,
        utterance: str,
        context: List[Dict[str, str]],
        focus: str,
        profile: Dict[str, Any],
        intensity: str,
        drill: Optional[Drill]
    ) -> str:
        """Internal method to build prompt and call LLM."""
        
        # 1. Prepare context string
        history_str = self._format_history(context)
        
        # 2. Prepare drill components
        drill_instruction = ""
        drill_guidance = ""
        if drill:
            drill_instruction = f"IMPORTANT: You must deliver this coaching drill: {drill.instruction}"
            drill_guidance = "Integrate the drill naturally. Do not ignore the user's message, but prioritize setting up the drill."
        
        # 3. Prepare profile defaults
        if not profile:
            profile = {"cefr_target": "B2", "accent_preference": "Neutral"}

        # 4. Build Prompt
        prompt = self.system_prompt_template.format(
            focus=focus,
            intensity=intensity,
            cefr=profile.get("cefr_target", "B2"),
            accent=profile.get("accent_preference", "Neutral"),
            drill_instruction=drill_instruction,
            history=history_str,
            user_utterance=utterance,
            drill_guidance=drill_guidance
        )

        # 5. Call LLM (Mock for now if no client)
        if self.llm_client:
            try:
                response = self.llm_client.generate(prompt, model=self.model_name)
                return response
            except Exception as e:
                print(f"LLM Error: {e}")
                return "I'm having a bit of trouble thinking right now, but let's keep chatting."
        else:
            # Mock response for testing/MVP without live LLM
            if drill:
                return f"[MOCK COACH] {drill.instruction}"
            else:
                return f"[MOCK COACH] That's interesting! Tell me more about {utterance}."

    def _format_history(self, context: List[Dict[str, str]]) -> str:
        """Format chat history for the prompt."""
        formatted = []
        # Take last 10 exchanges to fit context window
        recent = context[-10:] 
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Coach"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
