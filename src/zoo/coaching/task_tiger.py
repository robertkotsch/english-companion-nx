"""TaskTiger agent for designing coaching drills.

TaskTiger receives prioritized signals from the Orchestrator and designs
specific, actionable drills for the user to practice.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import random
import time
import uuid

from src.zoo.signals import (
    Signal,
    SIGNAL_GRAMMAR_ERROR,
    SIGNAL_FILLER_DETECTED,
    SIGNAL_VOCAB_OPPORTUNITY,
    SIGNAL_VOCAB_USED
)
from src.zoo.zoo_logger import get_zoo_logger

# Drill Types
DRILL_TYPE_FILLER = "filler"
DRILL_TYPE_GRAMMAR = "grammar"
DRILL_TYPE_VOCAB = "vocab"

# Filler Drill Variants
FILLER_VARIANT_STANDARD = "standard"
FILLER_VARIANT_PAUSE = "pause"
FILLER_VARIANT_BREATH = "breath"

@dataclass
class Drill:
    """A specific practice task for the user."""
    type: str  # filler, grammar, vocab
    instruction: str  # Text to be spoken by CoachCoyote
    target_content: str  # The specific word/sentence to practice
    expected_response_type: str  # "repeat", "reformulate", "create_sentence"
    variant: Optional[str] = None  # For specific drill subtypes
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)

class TaskTiger:
    """Agent responsible for designing drills based on signals."""

    def __init__(self):
        self.drill_history: List[Drill] = []
        self.logger = get_zoo_logger()

    def design_drill(self, signal: Signal, context: str = "") -> Optional[Drill]:
        """Generate a drill based on the provided signal.
        
        Args:
            signal: The signal triggering the drill.
            context: The conversation context (optional).
            
        Returns:
            A Drill object or None if no drill could be designed.
        """
        if signal.type == SIGNAL_FILLER_DETECTED:
            drill = self._design_filler_drill(signal)
        elif signal.type == SIGNAL_GRAMMAR_ERROR:
            drill = self._design_grammar_drill(signal)
        elif signal.type == SIGNAL_VOCAB_OPPORTUNITY:
            drill = self._design_vocab_drill(signal)
        else:
            drill = None
        
        if drill:
            self.logger.info("TaskTiger", f"Designed {drill.type} drill: {drill.instruction[:50]}...")
        
        return drill

    def _design_filler_drill(self, signal: Signal) -> Drill:
        """Design a drill to reduce filler usage."""
        filler = signal.data.get("filler", "um")
        
        # Randomly select a variant, favoring pedagogical best practices (Pause/Breath)
        # 20% Standard, 40% Pause, 40% Breath
        roll = random.random()
        if roll < 0.2:
            variant = FILLER_VARIANT_STANDARD
            instruction = f"Let's try that sentence again, but this time without saying '{filler}'."
        elif roll < 0.6:
            variant = FILLER_VARIANT_PAUSE
            instruction = f"Try that sentence again. Instead of '{filler}', just pause for a second to gather your thoughts."
        else:
            variant = FILLER_VARIANT_BREATH
            instruction = f"Repeat that thought, but take a deep breath where you would normally say '{filler}'."

        return Drill(
            type=DRILL_TYPE_FILLER,
            instruction=instruction,
            target_content=filler,
            expected_response_type="reformulate",
            variant=variant,
            metadata={"original_signal": signal.to_dict()}
        )

    def _design_grammar_drill(self, signal: Signal) -> Drill:
        """Design a drill to correct a grammar error."""
        original = signal.data.get("original", "")
        suggestion = signal.data.get("suggestion", "")
        error_type = signal.data.get("error_type", "grammar")

        if suggestion:
            instruction = f"I noticed a small slip with {error_type}. Try saying: '{suggestion}'."
            target = suggestion
        else:
            # Fallback if no specific suggestion is available (should be rare with GrammarGiraffe)
            instruction = f"Can you try rephrasing '{original}' to fix the {error_type}?"
            target = original

        return Drill(
            type=DRILL_TYPE_GRAMMAR,
            instruction=instruction,
            target_content=target,
            expected_response_type="repeat" if suggestion else "reformulate",
            metadata={"original_signal": signal.to_dict()}
        )

    def _design_vocab_drill(self, signal: Signal) -> Drill:
        """Design a drill to encourage vocabulary usage."""
        word = signal.data.get("word", "")
        definition = signal.data.get("definition", "")
        
        instruction = f"That's a good opportunity to use the word '{word}'. Can you try using it in a sentence?"
        if definition:
             instruction += f" It means {definition}."

        return Drill(
            type=DRILL_TYPE_VOCAB,
            instruction=instruction,
            target_content=word,
            expected_response_type="create_sentence",
            metadata={"original_signal": signal.to_dict()}
        )

    def validate_attempt(self, drill: Drill, user_response: str) -> bool:
        """Check if the user's response satisfies the drill.
        
        Args:
            drill: The drill that was assigned.
            user_response: What the user said.
            
        Returns:
            True if successful, False otherwise.
        """
        # MVP Validation Logic: Simple checks
        
        if drill.type == DRILL_TYPE_FILLER:
            # Check if the filler word is absent
            filler = drill.target_content.lower()
            return filler not in user_response.lower().split()
            
        elif drill.type == DRILL_TYPE_GRAMMAR:
            # If we gave a suggestion, check if they said it (fuzzy match or exact)
            # For MVP, let's check if the suggestion is roughly in the response
            if drill.expected_response_type == "repeat":
                # Remove punctuation and lowercase for comparison
                target_clean = self._clean_text(drill.target_content)
                response_clean = self._clean_text(user_response)
                return target_clean in response_clean
            return True # Reformulation is harder to validate without LLM, assume effort = success for MVP

        elif drill.type == DRILL_TYPE_VOCAB:
            # Check if the target word is in the response
            word = drill.target_content.lower()
            return word in user_response.lower()
            
        return False

    def _clean_text(self, text: str) -> str:
        """Helper to normalize text for comparison."""
        import string
        return text.lower().translate(str.maketrans('', '', string.punctuation)).strip()
