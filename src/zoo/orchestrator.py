"""Orchestrator agent for the Zoo system.

The OrchestratorOctopus is the central decision-making brain. It collects signals
from Listener agents, prioritizes them based on context and configuration, and
decides on the appropriate action (e.g., trigger a drill, buffer for later, or ignore).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
import time
import logging

from src.zoo.signals import Signal, SIGNAL_GRAMMAR_ERROR, SIGNAL_FILLER_DETECTED, SIGNAL_VOCAB_OPPORTUNITY, SIGNAL_VOCAB_USED
from src.zoo.zoo_logger import get_zoo_logger

class ActionType(Enum):
    """Types of actions the Orchestrator can decide on."""
    DRILL_NOW = "drill_now"       # Interrupt/respond with a drill immediately
    BUFFER = "buffer"             # Save for end-of-session summary
    IGNORE = "ignore"             # Low priority, log only
    PASS_THROUGH = "pass_through" # Normal conversation continues (no intervention)

@dataclass
class Action:
    """Decision made by the Orchestrator."""
    type: ActionType
    signal: Optional[Signal] = None
    reason: str = ""
    score: float = 0.0

class OrchestratorOctopus:
    """Central decision-making agent."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Orchestrator.

        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        self.logger = get_zoo_logger()
        self.last_drill_time = 0.0
        self.drill_cooldown_sec = self.config.get("drill_cooldown_sec", 60.0) # Minimum time between drills
        self.max_drills_per_session = self.config.get("max_drills_per_session", 10)
        self.drills_this_session = 0
        
        # Session context (would be updated by SessionShepherd/FocusFalcon in full system)
        self.current_focus = self.config.get("default_focus", "general") 
        self.coach_intensity = self.config.get("coach_intensity", "normal") # off, soft, normal

    def process_utterance(self, utterance: str, signals: List[Signal]) -> Action:
        """Process signals for a single utterance and decide on an action.

        Args:
            utterance: The user's spoken text.
            signals: List of signals emitted by Listeners for this utterance.

        Returns:
            Action: The decided action.
        """
        if not signals:
            return Action(ActionType.PASS_THROUGH, reason="No signals")

        # 1. Score all signals
        scored_signals = []
        for signal in signals:
            score = self._score_signal(signal)
            scored_signals.append((score, signal))

        # 2. Sort by score (descending)
        scored_signals.sort(key=lambda x: x[0], reverse=True)

        if not scored_signals:
             return Action(ActionType.PASS_THROUGH, reason="No scored signals")

        top_score, top_signal = scored_signals[0]

        # 3. Decide action based on top signal
        action = self._decide_action(top_signal, top_score)
        
        # Log the decision
        self.logger.orchestrator_decision(
            action.type.value,
            len(signals),
            f"{action.reason} (top signal: {top_signal.type}, score: {top_score:.1f})"
        )
        
        # 4. Update state if we decided to drill
        if action.type == ActionType.DRILL_NOW:
            self.last_drill_time = time.time()
            self.drills_this_session += 1

        return action

    def _score_signal(self, signal: Signal) -> float:
        """Calculate a priority score for a signal (0.0 - 10.0)."""
        score = signal.severity * 5.0 # Base score from severity (0-5)

        # Boost based on focus area
        if self.current_focus == "grammar" and signal.type == SIGNAL_GRAMMAR_ERROR:
            score *= 1.5
        elif self.current_focus == "fillers" and signal.type == SIGNAL_FILLER_DETECTED:
            score *= 1.5
        elif self.current_focus == "vocab" and signal.type in (SIGNAL_VOCAB_OPPORTUNITY, SIGNAL_VOCAB_USED):
            score *= 1.5

        # Boost if realtime is desirable
        if signal.realtime_desirable:
            score += 2.0

        return score

    def _decide_action(self, signal: Signal, score: float) -> Action:
        """Determine the action based on the signal and its score."""
        
        # Check global constraints
        if self.coach_intensity == "off":
            return Action(ActionType.BUFFER, signal=signal, reason="Coach mode is off", score=score)

        # Check drill cooldown
        time_since_last_drill = time.time() - self.last_drill_time
        if time_since_last_drill < self.drill_cooldown_sec:
             return Action(ActionType.BUFFER, signal=signal, reason=f"Drill cooldown ({int(time_since_last_drill)}s < {self.drill_cooldown_sec}s)", score=score)
        
        # Check session limits
        if self.drills_this_session >= self.max_drills_per_session:
             return Action(ActionType.BUFFER, signal=signal, reason="Max drills reached", score=score)

        # Thresholds for action
        DRILL_THRESHOLD = 6.0
        BUFFER_THRESHOLD = 2.0

        if score >= DRILL_THRESHOLD:
            return Action(ActionType.DRILL_NOW, signal=signal, reason=f"Score {score:.1f} >= {DRILL_THRESHOLD}", score=score)
        elif score >= BUFFER_THRESHOLD:
            return Action(ActionType.BUFFER, signal=signal, reason=f"Score {score:.1f} >= {BUFFER_THRESHOLD}", score=score)
        else:
            return Action(ActionType.IGNORE, signal=signal, reason=f"Score {score:.1f} too low", score=score)

    def reset_session(self):
        """Reset session-specific counters."""
        self.drills_this_session = 0
        self.last_drill_time = 0.0
