"""Base class for all Listener agents.

Listeners are passive observer agents that analyze user utterances
and emit signals to the OrchestratorOctopus.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..signals import Signal


class BaseListener(ABC):
    """Abstract base class for Listener agents.

    All Listener agents must inherit from this class and implement
    the process_utterance method.

    Listeners are stateless analyzers that:
    1. Receive a user utterance (text + optional metadata)
    2. Analyze it for specific patterns/issues
    3. Emit zero or more Signals

    Example:
        class FillerFalcon(BaseListener):
            def process_utterance(self, text, metadata):
                # Detect filler words
                signals = []
                if "um" in text:
                    signals.append(create_filler_signal(...))
                return signals
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the listener.

        Args:
            config: Optional configuration dictionary for tuning thresholds
        """
        self.config = config or {}
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        """Get the listener's name (class name by default)."""
        return self._name

    @abstractmethod
    def process_utterance(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        """Process a user utterance and emit signals.

        This is the main method that all Listeners must implement.

        Args:
            text: The user's utterance (transcribed text)
            metadata: Optional metadata about the utterance:
                - utterance_id: str - Unique identifier
                - timestamp: float - When utterance occurred
                - duration_ms: int - How long utterance took
                - word_timestamps: List[Dict] - Word-level timing (if available)
                - context: List[Dict] - Recent conversation history
                - session_id: str - Current session identifier

        Returns:
            List of Signal objects (empty list if no issues detected)

        Raises:
            Exception subclasses if processing fails (should be caught by caller)
        """
        pass

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with fallback to default.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def __repr__(self) -> str:
        """String representation of the listener."""
        return f"{self._name}(config={self.config})"


class ListenerError(Exception):
    """Base exception for listener processing errors."""
    pass


class ListenerConfigError(ListenerError):
    """Raised when listener configuration is invalid."""
    pass


class ListenerProcessingError(ListenerError):
    """Raised when listener fails to process an utterance."""
    pass
