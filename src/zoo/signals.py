"""Signal system for Zoo agent communication.

Signals are emitted by Listener agents to communicate observations
about user utterances to the OrchestratorOctopus.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Literal
import time
import uuid


# Signal scope types
ScopeType = Literal["utterance", "session", "trend"]

# Signal type constants
SIGNAL_GRAMMAR_ERROR = "grammar_error"
SIGNAL_FILLER_DETECTED = "filler_detected"
SIGNAL_VOCAB_OPPORTUNITY = "vocab_opportunity"
SIGNAL_VOCAB_USED = "vocab_used"
SIGNAL_TEMPO_ISSUE = "tempo_issue"


@dataclass
class Signal:
    """Signal emitted by a Listener agent.

    Attributes:
        source: Agent name that emitted the signal (e.g., "GrammarGiraffe")
        type: Signal category (e.g., "grammar_error", "filler_detected")
        severity: Importance/urgency of the signal (0.0 = info, 1.0 = critical)
        scope: Temporal scope of the signal
            - "utterance": Specific to current utterance
            - "session": Aggregated over session
            - "trend": Long-term pattern
        realtime_desirable: Should this trigger immediate action vs buffering?
        data: Signal-specific payload (error details, counts, etc.)
        timestamp: Unix timestamp when signal was created
        utterance_id: Identifier linking signal to specific utterance
    """
    source: str
    type: str
    severity: float
    scope: ScopeType
    realtime_desirable: bool
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    utterance_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate signal fields."""
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError(f"Severity must be 0.0-1.0, got {self.severity}")

        if self.scope not in ("utterance", "session", "trend"):
            raise ValueError(f"Invalid scope: {self.scope}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary for logging/serialization."""
        return {
            "source": self.source,
            "type": self.type,
            "severity": self.severity,
            "scope": self.scope,
            "realtime_desirable": self.realtime_desirable,
            "data": self.data,
            "timestamp": self.timestamp,
            "utterance_id": self.utterance_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Signal":
        """Create Signal from dictionary."""
        return cls(
            source=d["source"],
            type=d["type"],
            severity=d["severity"],
            scope=d["scope"],
            realtime_desirable=d["realtime_desirable"],
            data=d["data"],
            timestamp=d.get("timestamp", time.time()),
            utterance_id=d.get("utterance_id", str(uuid.uuid4())),
        )


# Convenience factory functions for common signal types

def create_grammar_signal(
    source: str,
    error_type: str,
    severity: float,
    original: str,
    suggestion: str = "",
    **extra_data
) -> Signal:
    """Create a grammar error signal.

    Args:
        source: Agent name (usually "GrammarGiraffe")
        error_type: Grammar category (articles, tense, word_order, etc.)
        severity: 0.0-1.0
        original: Original problematic text
        suggestion: Suggested correction (optional)
        **extra_data: Additional context
    """
    return Signal(
        source=source,
        type=SIGNAL_GRAMMAR_ERROR,
        severity=severity,
        scope="utterance",
        realtime_desirable=severity > 0.7,  # Only critical errors trigger drills
        data={
            "error_type": error_type,
            "original": original,
            "suggestion": suggestion,
            **extra_data,
        }
    )


def create_filler_signal(
    source: str,
    filler_word: str,
    position: int,
    total_count: int,
    rate_per_min: float,
) -> Signal:
    """Create a filler word detection signal.

    Args:
        source: Agent name (usually "FillerFalcon")
        filler_word: Detected filler ("um", "uh", "like", etc.)
        position: Word position in utterance
        total_count: Total fillers in current utterance
        rate_per_min: Filler rate over recent history
    """
    severity = min(1.0, rate_per_min / 10.0)  # >10/min = max severity
    return Signal(
        source=source,
        type=SIGNAL_FILLER_DETECTED,
        severity=severity,
        scope="utterance",
        realtime_desirable=total_count >= 3,  # 3+ fillers in one utterance
        data={
            "filler": filler_word,
            "position": position,
            "count": total_count,
            "rate_per_min": rate_per_min,
        }
    )


def create_vocab_signal(
    source: str,
    signal_type: str,  # vocab_used or vocab_opportunity
    word: str,
    severity: float,
    **extra_data
) -> Signal:
    """Create a vocabulary-related signal.

    Args:
        source: Agent name (usually "LexiLynx")
        signal_type: "vocab_used" or "vocab_opportunity"
        word: Target vocabulary word
        severity: 0.0-1.0
        **extra_data: Context (correct usage, missed opportunity, etc.)
    """
    return Signal(
        source=source,
        type=signal_type,
        severity=severity,
        scope="utterance",
        realtime_desirable=signal_type == "vocab_opportunity" and severity > 0.6,
        data={
            "word": word,
            **extra_data,
        }
    )


def create_tempo_signal(
    source: str,
    issue_type: str,  # "too_slow", "too_fast", "long_pause"
    wpm: float,
    severity: float,
    **extra_data
) -> Signal:
    """Create a tempo/pacing signal.

    Args:
        source: Agent name (usually "TempoTiger")
        issue_type: Type of pacing issue
        wpm: Words per minute measurement
        severity: 0.0-1.0
        **extra_data: Additional context (pause locations, etc.)
    """
    return Signal(
        source=source,
        type=SIGNAL_TEMPO_ISSUE,
        severity=severity,
        scope="session",  # Tempo is usually session-level trend
        realtime_desirable=False,  # Don't interrupt for pacing
        data={
            "issue_type": issue_type,
            "wpm": wpm,
            **extra_data,
        }
    )
