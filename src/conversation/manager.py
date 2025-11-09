"""
Conversation manager for English Companion NX
Manages conversation context, history, and system prompts
"""

from typing import List, Dict, Optional
from pathlib import Path
from src.core.config import Config
from src.conversation.llm_client import OllamaClient


class ConversationManager:
    """Manages conversation state and context"""

    # Fallback system prompt if personality file not found
    DEFAULT_SYSTEM_PROMPT = """You are a friendly, patient English conversation partner for an adult learner.

Your primary goal is to have genuine, engaging conversations. The user is practicing English and wants someone to talk to regularly.

Core Behaviors:
- Be genuinely interested in what the user says
- Ask thoughtful follow-up questions
- Share opinions and perspectives (have personality)
- Keep responses conversational and natural (2-3 sentences typically)
- Stay positive and encouraging

Language Learning Support:
- Occasionally and gently correct grammar errors (max 1 per conversation)
- Introduce new vocabulary naturally in context
- Rephrase complex sentences if the user seems confused
- Prioritize communication over perfect accuracy

Remember: You're a companion first, teacher second. Keep it conversational!"""

    def __init__(self, context_size: Optional[int] = None):
        """
        Initialize conversation manager

        Args:
            context_size: Maximum number of exchanges to keep in context
        """
        self.context_size = context_size or Config.CONVERSATION_CONTEXT_SIZE
        self.llm_client = OllamaClient()

        # Load personality prompt from file
        system_prompt = self._load_personality()

        # Initialize conversation history with system prompt
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

    def _load_personality(self) -> str:
        """
        Load personality prompt from file based on config

        Returns:
            System prompt text
        """
        # Get project root (3 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        personality_file = project_root / "personalities" / f"{Config.PERSONALITY_PROFILE}.txt"

        try:
            if personality_file.exists():
                return personality_file.read_text().strip()
            else:
                print(f"Warning: Personality file not found: {personality_file}")
                print(f"Using default personality prompt")
                return self.DEFAULT_SYSTEM_PROMPT
        except Exception as e:
            print(f"Error loading personality file: {e}")
            print(f"Using default personality prompt")
            return self.DEFAULT_SYSTEM_PROMPT

    def add_user_message(self, message: str):
        """Add user message to history"""
        self.history.append({
            "role": "user",
            "content": message
        })

    def add_assistant_message(self, message: str):
        """Add assistant message to history"""
        self.history.append({
            "role": "assistant",
            "content": message
        })

    def generate_response(self, user_message: str) -> str:
        """
        Generate response to user message

        Args:
            user_message: User's message

        Returns:
            Generated response
        """
        # Add user message to history
        self.add_user_message(user_message)

        # Prune history if needed (keep system prompt + last N exchanges)
        self._prune_history()

        # Generate response
        response = self.llm_client.generate_response(
            user_message="",  # Already in history
            conversation_history=self.history
        )

        # Add response to history
        self.add_assistant_message(response)

        return response

    def _prune_history(self):
        """Prune conversation history to stay within context size"""
        # Always keep system prompt (index 0)
        # Keep last N exchanges (user + assistant pairs)

        if len(self.history) <= self.context_size * 2 + 1:
            return  # Within limit

        # Calculate how many messages to keep (system + last N exchanges)
        messages_to_keep = self.context_size * 2  # N user + N assistant messages

        # Keep system prompt + last N exchanges
        self.history = [self.history[0]] + self.history[-messages_to_keep:]

    def get_context_summary(self) -> str:
        """Get summary of current conversation context"""
        user_messages = [m for m in self.history if m["role"] == "user"]
        assistant_messages = [m for m in self.history if m["role"] == "assistant"]

        return (
            f"Exchanges: {len(user_messages)}, "
            f"Context size: {len(self.history) - 1}/{self.context_size * 2}"
        )

    def clear_history(self):
        """Clear conversation history (keep system prompt)"""
        self.history = [self.history[0]]
